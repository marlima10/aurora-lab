"""Private raster gallery. Originals stay on disk; only metadata-free JPEGs are served."""
import hashlib
import io
import os
import re
import secrets
import stat
import threading
import warnings
from pathlib import Path
from PIL import Image,ImageOps

MAX_BYTES=12*1024*1024
MAX_IMAGES=50
MAX_PIXELS=50_000_000
ID=re.compile(r'^[a-f0-9]{64}$')
Image.MAX_IMAGE_PIXELS=MAX_PIXELS

class Gallery:
 def __init__(self,root):
  self.root=Path(root);self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
  self.cache=self.root/'.rendered';self.cache.mkdir(mode=0o700,exist_ok=True)
  if self.root.is_symlink() or self.cache.is_symlink():raise ValueError('Pasta de imagens inválida.')
  self.lock=threading.RLock();self.known={}
 def decode(self,raw):
  if not 0<len(raw)<=MAX_BYTES:raise ValueError('Envie uma imagem de até 12 MB.')
  try:
   with warnings.catch_warnings():
    warnings.simplefilter('error',Image.DecompressionBombWarning)
    with Image.open(io.BytesIO(raw)) as source:
     if source.format not in ('JPEG','PNG','WEBP') or getattr(source,'n_frames',1)!=1:raise ValueError('Use JPG, PNG ou WebP sem animação.')
     if source.width*source.height>MAX_PIXELS:raise ValueError('A imagem deve ter no máximo 50 megapixels.')
     kind=source.format;source.verify()
    with Image.open(io.BytesIO(raw)) as source:
     source.draft('RGB',(2560,1600));source.thumbnail((2560,1600))
     image=ImageOps.exif_transpose(source).convert('RGB')
     full=io.BytesIO();image.save(full,format='JPEG',quality=85)
     image.thumbnail((480,320));thumb=io.BytesIO();image.save(thumb,format='JPEG',quality=78)
   return full.getvalue(),thumb.getvalue(),{'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[kind]
  except (OSError,SyntaxError,Image.DecompressionBombError,Image.DecompressionBombWarning) as error:
   raise ValueError('O arquivo não é uma imagem válida ou é grande demais.') from error
 def atomic(self,path,raw):
  temp=path.with_name('.'+secrets.token_hex(12)+'.tmp')
  try:
   with temp.open('xb') as handle:handle.write(raw)
   temp.replace(path)
  finally:temp.unlink(missing_ok=True)
 def read_source(self,path):
  flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)
  fd=os.open(path,flags)
  with os.fdopen(fd,'rb') as handle:
   info=os.fstat(handle.fileno())
   if not stat.S_ISREG(info.st_mode) or not 0<info.st_size<=MAX_BYTES:raise ValueError('Arquivo inválido.')
   return handle.read(MAX_BYTES+1),info
 def scan(self):
  with self.lock:
   items=[];skipped=0;seen=set();live={}
   for path in sorted(self.root.iterdir(),key=lambda p:p.name.casefold())[:200]:
    if path.name.startswith('.'):continue
    if len(items)>=MAX_IMAGES:skipped+=1;continue
    if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ('.jpg','.jpeg','.png','.webp'):
     skipped+=1;continue
    try:
     info=path.stat();stamp=(info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
     old=self.known.get(path.name)
     if old and not (self.cache/(old[1]+'.jpg')).is_symlink() and not (self.cache/(old[1]+'.thumb.jpg')).is_symlink() and old[0]==stamp and (self.cache/(old[1]+'.jpg')).is_file() and (self.cache/(old[1]+'.thumb.jpg')).is_file():identifier=old[1]
     else:
      raw,info=self.read_source(path);identifier=hashlib.sha256(raw).hexdigest();full,thumb,_=self.decode(raw)
      self.atomic(self.cache/(identifier+'.jpg'),full);self.atomic(self.cache/(identifier+'.thumb.jpg'),thumb)
      stamp=(info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
     live[path.name]=(stamp,identifier)
     if identifier in seen:continue
     seen.add(identifier)
     if len(items)>=MAX_IMAGES:skipped+=1;continue
     items.append({'id':identifier,'name':path.name,'url':'/auth/mirror/backgrounds/'+identifier,'thumbnail':'/auth/mirror/backgrounds/'+identifier+'/thumb'})
    except (OSError,ValueError):skipped+=1
   self.known=live
   return {'images':items,'skipped':skipped,'maxImages':MAX_IMAGES,'maxBytes':MAX_BYTES}
 def upload(self,raw,name='imagem'):
  with self.lock:
   full,thumb,extension=self.decode(raw);identifier=hashlib.sha256(raw).hexdigest()
   listing=self.scan()
   if any(item['id']==identifier for item in listing['images']):return listing|{'uploadedId':identifier,'duplicate':True}
   if len(listing['images'])>=MAX_IMAGES:raise ValueError('Limite de 50 imagens atingido.')
   stem=''.join(c for c in Path(name.replace('\\','/')).stem if c.isalnum() or c in ' -_')[:70].strip() or 'imagem'
   self.atomic(self.root/(stem+'-'+identifier[:12]+extension),raw)
   self.atomic(self.cache/(identifier+'.jpg'),full);self.atomic(self.cache/(identifier+'.thumb.jpg'),thumb)
   return self.scan()|{'uploadedId':identifier,'duplicate':False}
 def image(self,identifier,thumb=False):
  if not ID.fullmatch(identifier):raise ValueError('Imagem inválida.')
  with self.lock:
   if not any(item['id']==identifier for item in self.scan()['images']):raise FileNotFoundError('Imagem não encontrada.')
   path=self.cache/(identifier+('.thumb.jpg' if thumb else '.jpg'))
   with os.fdopen(os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)),'rb') as handle:return handle.read(MAX_BYTES+1)
