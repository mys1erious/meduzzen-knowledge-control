from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


# Added to match the tests e.g.:
#   response.json().get("result").get("users") == []
def response_with_result_key(schema, status_code=200):
    return JSONResponse(
        content={'result': jsonable_encoder(schema)},
        status_code=status_code
    )


def exclude_none(original: dict):
    return {k: v for k, v in original.items() if v is not None}
