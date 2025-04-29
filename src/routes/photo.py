from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import aiohttp
from config.settings import settings

router = APIRouter()


@router.get('/photo/{photo_path:path}')
async def get_photo(photo_path: str) -> StreamingResponse:
    """
    Proxy endpoint to serve photos from MinIO.
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Ensure the photo_path is properly encoded
            minio_url = f'{settings.MINIO_URL}/{photo_path}'
            async with session.get(minio_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=404, detail='Photo not found')

                return StreamingResponse(
                    response.content, media_type=response.headers.get('Content-Type', 'image/jpeg')
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
