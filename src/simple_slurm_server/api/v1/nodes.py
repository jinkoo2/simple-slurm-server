from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Path

from ... import slurm_commands as sl

router = APIRouter()


@router.get(
    "/nodes",
    response_model=List[Dict[str, Any]],
    summary="List nodes",
    description="Return SLURM node information (from sinfo), one entry per node.",
    responses={
        200: {"description": "List of node summaries."},
        500: {"description": "SLURM or server error."},
    },
)
async def list_nodes():
    try:
        return sl.get_nodes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sinfo",
    response_model=List[Dict[str, Any]],
    summary="Get sinfo output",
    description="Return sinfo output: one row per partition/state/nodelist combination.",
    responses={
        200: {"description": "List of sinfo rows."},
        500: {"description": "SLURM or server error."},
    },
)
async def get_sinfo_data():
    try:
        return sl.get_sinfo()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/partitions/{partition_name}",
    response_model=Dict[str, Any],
    summary="Get partition details",
    description="Return details of a SLURM partition (from scontrol show partition + sinfo).",
    responses={
        200: {"description": "Partition details."},
        500: {"description": "SLURM or server error."},
    },
)
async def get_partition_details(
    partition_name: str = Path(..., description="SLURM partition name."),
):
    try:
        return sl.get_partition(partition_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/nodes/{node_name}",
    response_model=Dict[str, Any],
    summary="Get node details",
    description="Return full details of a single SLURM node (from scontrol show node).",
    responses={
        200: {"description": "Node details (key-value pairs from SLURM)."},
        500: {"description": "SLURM or server error."},
    },
)
async def get_node(
    node_name: str = Path(..., description="SLURM node name."),
):
    try:
        return sl.get_node(node_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
