from typing import Sequence, TypeVar, Optional, Callable, Any

from fastapi_pagination import paginate as _paginate
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.types import AdditionalData


T = TypeVar("T")


def paginate(
        sequence: Sequence[T],
        params: Optional[AbstractParams] = None,
        length_function: Callable[[Sequence[T]], int] = len,
        items_name: str = '',
        additional_data: AdditionalData = None,
) -> Any:
    pagination = vars(_paginate(
        sequence,
        params,
        length_function,
        additional_data=additional_data
    ))
    if items_name:
        pagination[items_name] = pagination.pop('items')
    return pagination
