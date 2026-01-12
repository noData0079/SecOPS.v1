
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.src.core.evolution.optimizers.text_gradient import TextGradientOptimizer
from backend.src.core.evolution.optimizers.mipro import MiproOptimizer
from backend.src.core.evolution.sentience import SentienceEngine

@pytest.mark.asyncio
async def test_text_gradient_optimizer():
    optimizer = TextGradientOptimizer()

    # Mock LLMRouter
    optimizer.router.generate = AsyncMock(side_effect=[
        "This response is incorrect because it misses X.", # Critique
        "<new_variable> You are a helpful agent that always includes X. </new_variable>" # Update
    ])

    new_prompt = await optimizer.optimize(
        current_prompt="You are a helpful agent.",
        task_description="Explain X",
        test_input="What is X?",
        test_output="It is a letter.",
        expected_output_description="Should explain X in detail."
    )

    assert "You are a helpful agent that always includes X." in new_prompt
    assert optimizer.router.generate.call_count == 2

@pytest.mark.asyncio
async def test_mipro_optimizer():
    optimizer = MiproOptimizer()

    # Mock LLMRouter
    # 1. Propose candidates (returns numbered list)
    # 2. Evaluate candidate 1
    # 3. Evaluate candidate 2 (and so on)
    optimizer.router.generate = AsyncMock(side_effect=[
        "1. Candidate A --- 2. Candidate B", # Proposal
        "Output A", # Eval 1
        "Output B", # Eval 2 (assuming num_candidates=2, but we also eval baseline so +1)
        "Output Baseline"
    ])

    # Simple evaluator function
    def evaluator(output, example):
        if "A" in output: return 1.0
        return 0.5

    dataset = [{'input': 'test', 'expected': 'A'}]

    best_prompt = await optimizer.optimize(
        base_prompt="Base Prompt",
        task_description="Do A",
        dataset=dataset,
        evaluator_func=evaluator,
        num_candidates=2
    )

    # Since Output A gets score 1.0, Candidate A (first one) should be chosen
    assert "Candidate A" in best_prompt or "Candidate A" == best_prompt

@pytest.mark.asyncio
async def test_sentience_engine():
    engine = SentienceEngine()

    # Mock internals
    engine.text_grad.optimize = AsyncMock(return_value="Optimized by TextGrad")
    engine.mipro.optimize = AsyncMock(return_value="Optimized by MIPRO")

    # Test 1: Recent failures -> TextGrad
    res1 = await engine.evolve_prompt(
        current_prompt="Prompt",
        task_description="Task",
        recent_failures=[{'input': 'i', 'output': 'o', 'expected': 'e'}]
    )
    assert res1 == "Optimized by TextGrad"

    # Test 2: Dataset -> MIPRO
    res2 = await engine.evolve_prompt(
        current_prompt="Prompt",
        task_description="Task",
        dataset=[{'input': 'i', 'expected': 'e'}],
        evaluator_func=lambda x,y: 1.0
    )
    assert res2 == "Optimized by MIPRO"
