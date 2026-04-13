"""Evaluation harness — run golden eval set against the FinOps agents using DeepEval."""

import asyncio
import json
from pathlib import Path

from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from fin_agent.agent import root_agent
from fin_agent.config import APP_NAME, DATA_DIR

EVAL_SET_PATH = DATA_DIR / "golden_eval_set.json"


async def _run_query(runner: Runner, session_service: InMemorySessionService, question: str) -> str:
    """Run a single query through the agent and return the final text response."""
    import uuid

    user_id = "eval_user"
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    user_content = types.Content(
        role="user", parts=[types.Part.from_text(text=question)]
    )

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=user_content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text

    return final_text


def run_eval():
    """Load golden eval set, run each question, and evaluate with DeepEval."""
    eval_data = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    test_cases: list[LLMTestCase] = []

    for item in eval_data:
        print(f"Running {item['id']}: {item['question'][:60]}...")
        actual = asyncio.run(_run_query(runner, session_service, item["question"]))

        tc = LLMTestCase(
            input=item["question"],
            actual_output=actual,
            expected_output=item["ground_truth"],
            context=[item["ground_truth"]],
        )
        test_cases.append(tc)
        print(f"  → Got {len(actual)} chars response")

    # Evaluate with DeepEval metrics
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
        HallucinationMetric(threshold=0.5),
    ]

    print(f"\nEvaluating {len(test_cases)} test cases with DeepEval...")
    results = evaluate(test_cases=test_cases, metrics=metrics)

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    for i, (item, tc) in enumerate(zip(eval_data, test_cases)):
        print(f"\n{item['id']} ({item['category']})")
        print(f"  Q: {item['question'][:80]}...")
        print(f"  A: {tc.actual_output[:120]}..." if len(tc.actual_output) > 120 else f"  A: {tc.actual_output}")

    return results


if __name__ == "__main__":
    run_eval()
