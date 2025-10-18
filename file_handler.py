import os
import secrets
from PIL import Image
from io import BytesIO

ALLOWED_MIME_TYPES={"image/jpeg","image/png","image/gif","image/webp"}
MAX_FILE_SIZE=8*1024*1024
CHUNK_SIZE=1024*1024
MAX_DIMENSION=1024

def save_profile_picture(file,user_id,old_picture_path=None):
    try:
        file.seek(0,2)
        file_size=file.tell()
        file.seek(0)
        if file_size>MAX_FILE_SIZE:
            return None,"File size exceeds 8MB limit"
        chunks=[]
        total_read=0
        while True:
            chunk=file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_read+=len(chunk)
            if total_read>MAX_FILE_SIZE:
                return None,"File size exceeds 8MB limit"
            chunks.append(chunk)
        file_data=b"".join(chunks)
        try:
            image=Image.open(BytesIO(file_data))
            image.verify()
            image=Image.open(BytesIO(file_data))
        except Exception:
            return None,"Invalid image file"
        mime_type=Image.MIME.get(image.format)
        if mime_type not in ALLOWED_MIME_TYPES:
            return None,"Only JPEG, PNG, GIF, and WebP images are allowed"
        width,height=image.size
        if width>MAX_DIMENSION or height>MAX_DIMENSION:
            image.thumbnail((MAX_DIMENSION,MAX_DIMENSION),Image.Resampling.LANCZOS)
        ext_map={"image/jpeg":".jpg","image/png":".png","image/gif":".gif","image/webp":".webp"}
        ext=ext_map.get(mime_type,".jpg")
        filename=f"{user_id}_{secrets.token_urlsafe(16)}{ext}"
        os.makedirs("data/uploads",exist_ok=True)
        filepath=os.path.join("data/uploads",filename)
        image.save(filepath,format=image.format,quality=95,optimize=True)
        if old_picture_path and os.path.exists(old_picture_path):
            try:
                os.remove(old_picture_path)
            except Exception:
                pass
        return filename,None
    except Exception as e:
        return None,f"Error processing file: {str(e)}"
