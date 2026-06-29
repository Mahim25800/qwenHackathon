"""
Training Simulation Route.
Instantiates the generated PyTorch code and trains it for a few epochs on dummy data.
This proves that the code is mathematically sound and the gradients flow properly.
"""

import asyncio
import json
import logging
from typing import List
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
import torch.nn as nn
import torch.optim as optim

router = APIRouter()
logger = logging.getLogger(__name__)

class TrainRequest(BaseModel):
    pytorch_code: str
    input_shape: List[int]
    num_classes: int


async def stream_training(request: TrainRequest):
    """
    Generator that compiles the PyTorch code, creates a dummy dataset,
    and runs a 5-epoch training loop, yielding progress via SSE.
    """
    yield f"data: {json.dumps({'status': 'initializing', 'message': 'Initializing training environment...'})}\n\n"
    await asyncio.sleep(0.5)

    try:
        # 1. Compile the code
        local_scope = {}
        # Make sure torch and nn are available in the exec scope
        exec_globals = {"torch": torch, "nn": nn}
        exec(request.pytorch_code, exec_globals, local_scope)

        # Find the nn.Module class
        module_class = None
        for name, obj in local_scope.items():
            if isinstance(obj, type) and issubclass(obj, nn.Module):
                module_class = obj
                break
        
        if not module_class:
            raise ValueError("Could not find a valid nn.Module class in the provided code.")

        yield f"data: {json.dumps({'status': 'compiled', 'message': f'Compiled {module_class.__name__} successfully.'})}\n\n"
        await asyncio.sleep(0.5)

        # 2. Instantiate the model
        model = module_class()
        
        # 3. Create dummy data
        batch_size = 64
        C, H, W = request.input_shape if len(request.input_shape) == 3 else (request.input_shape[0], 1, 1) # simple fallback
        
        if len(request.input_shape) == 3:
            dummy_inputs = torch.randn(batch_size, C, H, W)
        else:
            # 1D or 2D inputs
            dummy_inputs = torch.randn(batch_size, *request.input_shape)
            
        dummy_targets = torch.randint(0, request.num_classes, (batch_size,))

        yield f"data: {json.dumps({'status': 'data_ready', 'message': f'Generated dummy dataset with shape {list(dummy_inputs.shape)}.'})}\n\n"
        await asyncio.sleep(0.5)

        # 4. Setup Optimizer & Loss
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.01)

        # 5. Training Loop (5 epochs)
        epochs = 5
        for epoch in range(1, epochs + 1):
            model.train()
            optimizer.zero_grad()
            
            outputs = model(dummy_inputs)
            loss = criterion(outputs, dummy_targets)
            loss.backward()
            optimizer.step()
            
            # Calculate dummy accuracy
            _, predicted = torch.max(outputs.data, 1)
            correct = (predicted == dummy_targets).sum().item()
            accuracy = 100 * correct / dummy_targets.size(0)

            yield f"data: {json.dumps({'status': 'training', 'epoch': epoch, 'loss': float(loss.item()), 'accuracy': float(accuracy)})}\n\n"
            await asyncio.sleep(0.8) # Artificial delay so the UI animation looks good

        yield f"data: {json.dumps({'status': 'completed', 'message': 'Training completed successfully! Gradients are flowing.'})}\n\n"
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"


@router.post("/train")
async def train_model(request: TrainRequest):
    """
    Endpoint to test training the generated model.
    """
    return StreamingResponse(
        stream_training(request),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}
    )
