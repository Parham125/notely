import os
from id_generator import generate_id
from PIL import Image
from io import BytesIO

ALLOWED_MIME_TYPES={"image/jpeg","image/png","image/gif","image/webp"}
CHUNK_SIZE=1024*1024

def save_image(file,max_file_size,max_dimension,upload_dir,filename_prefix="",old_file_path=None):
    try:
        file.seek(0,2)
        file_size=file.tell()
        file.seek(0)
        max_size_mb=max_file_size//(1024*1024)
        if file_size>max_file_size:
            return None,f"File size exceeds {max_size_mb}MB limit"
        chunks=[]
        total_read=0
        while True:
            chunk=file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_read+=len(chunk)
            if total_read>max_file_size:
                return None,f"File size exceeds {max_size_mb}MB limit"
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
        if width>max_dimension or height>max_dimension:
            image.thumbnail((max_dimension,max_dimension),Image.Resampling.LANCZOS)
        ext_map={"image/jpeg":".jpg","image/png":".png","image/gif":".gif","image/webp":".webp"}
        ext=ext_map.get(mime_type,".jpg")
        filename=f"{filename_prefix}{(generate_id())}{ext}"
        os.makedirs(upload_dir,exist_ok=True)
        filepath=os.path.join(upload_dir,filename)
        image.save(filepath,format=image.format,quality=95,optimize=True)
        if old_file_path and os.path.isfile(old_file_path):
            try:
                os.remove(old_file_path)
            except:
                pass
        return filename,None
    except Exception as e:
        return None,f"Error processing file: {str(e)}"

def save_profile_picture(file,user_id,old_picture_path=None):
    filename,error=save_image(file,8*1024*1024,1024,"data/uploads",f"{user_id}_",old_picture_path)
    return filename,error

def save_blog_image(file):
    filename,error=save_image(file,8*1024*1024,1920,"data/uploads/blog_images","")
    return filename,error
