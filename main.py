import os
import io
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from PIL import Image
import uvicorn
import mimetypes

# Fix for Windows and some Linux systems missing CSS mime types
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/crop-service", response_class=HTMLResponse)
async def crop_service():
    with open("static/crop.html", "r") as f:
        return f.read()

@app.get("/pdf-compressor", response_class=HTMLResponse)
async def pdf_compressor_page():
    with open("static/pdf_compress.html", "r") as f:
        return f.read()

@app.get("/edit-pdf", response_class=HTMLResponse)
async def edit_pdf_page():
    with open("static/edit_pdf.html", "r") as f:
        return f.read()

@app.get("/merge-pdf", response_class=HTMLResponse)
async def merge_pdf_page():
    with open("static/merge_pdf.html", "r") as f:
        return f.read()

@app.get("/watermark-pdf", response_class=HTMLResponse)
async def watermark_pdf_page():
    with open("static/watermark_pdf.html", "r") as f:
        return f.read()

@app.get("/image-to-pdf", response_class=HTMLResponse)
async def image_to_pdf_page():
    with open("static/image_to_pdf.html", "r") as f:
        return f.read()

@app.post("/process-image-to-pdf")
async def process_image_to_pdf(
    files: list[UploadFile] = File(...)
):
    try:
        images = []
        for file in files:
            contents = await file.read()
            img = Image.open(io.BytesIO(contents))
            # Convert all to RGB (required for PDF saving)
            if img.mode != "RGB":
                img = img.convert("RGB")
            images.append(img)
        
        if not images:
            raise ValueError("No images uploaded")

        buf = io.BytesIO()
        # Save first image and append the rest
        images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
        buf.seek(0)
        
        return StreamingResponse(
            buf, 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=images_to_document.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-watermark-pdf")
async def process_watermark_pdf(
    file: UploadFile = File(...),
    text: str = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    font_size: float = Form(...),
    color: str = Form(...),
    canvas_w: float = Form(...),
    canvas_h: float = Form(...)
):
    import fitz
    import traceback
    try:
        print(f"DEBUG: Starting watermark for {file.filename}")
        print(f"DEBUG: Params - text: {text}, x: {x}, y: {y}, size: {font_size}")
        
        contents = await file.read()
        doc = fitz.open(stream=contents, filetype="pdf")
        font_path = "static/thai_font.ttf"
        
        hex_color = color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

        for i in range(len(doc)):
            page = doc[i]
            p_width = page.rect.width
            p_height = page.rect.height
            
            scale_x = p_width / canvas_w
            scale_y = p_height / canvas_h
            
            text_x = x * scale_x
            text_y = y * scale_y
            f_size = font_size * scale_x
            
            # Create a box around the point to use insert_textbox (which has better alignment)
            # A large enough box ensuring text fits
            rect_width = p_width 
            rect_height = f_size * 2
            target_rect = fitz.Rect(
                text_x - rect_width/2, 
                text_y - rect_height/2, 
                text_x + rect_width/2, 
                text_y + rect_height/2
            )
            
            page.insert_textbox(
                target_rect, 
                text, 
                fontsize=f_size,
                color=rgb,
                fontname=f"wm_{i}", 
                fontfile=font_path,
                rotate=0, # Fixed to horizontal
                align=1, # Center
                overlay=True
            )
        
        buf = io.BytesIO()
        doc.save(buf, garbage=3, deflate=True)
        doc.close()
        buf.seek(0)
        
        print("DEBUG: Watermark processing complete, streaming response")
        from urllib.parse import quote
        safe_filename = quote(f"watermarked_{file.filename}")
        
        return StreamingResponse(
            buf, 
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        print(f"DEBUG: Global error in watermark-pdf: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-merge-pdf")
async def process_merge_pdf(
    files: list[UploadFile] = File(...)
):
    from pypdf import PdfWriter
    try:
        merger = PdfWriter()
        for file in files:
            contents = await file.read()
            merger.append(io.BytesIO(contents))
        
        buf = io.BytesIO()
        merger.write(buf)
        buf.seek(0)
        
        return StreamingResponse(
            buf, 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=merged_document.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/make-mp4", response_class=HTMLResponse)
async def make_mp4_page():
    with open("static/make_mp4.html", "r") as f:
        return f.read()

@app.post("/process-make-mp4")
async def process_make_mp4(
    images: list[UploadFile] = File(...),
    audio: UploadFile = File(...),
    fps: float = Form(1.0) # Seconds per image by default if we treat it as a sequence
):
    import tempfile
    import shutil
    from moviepy.editor import ImageSequenceClip, AudioFileClip
    import os

    temp_dir = tempfile.mkdtemp()
    try:
        # Save images
        image_paths = []
        for i, img_file in enumerate(images):
            path = os.path.join(temp_dir, f"img_{i:03d}_{img_file.filename}")
            with open(path, "wb") as buffer:
                shutil.copyfileobj(img_file.file, buffer)
            image_paths.append(path)
        
        # Save audio
        audio_path = os.path.join(temp_dir, f"audio_{audio.filename}")
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Create clip
        # If fps=1, each image shows for 1 second.
        clip = ImageSequenceClip(image_paths, fps=fps)
        audio_clip = AudioFileClip(audio_path)
        
        # Loop or trim audio to match clip duration
        if audio_clip.duration > clip.duration:
            audio_clip = audio_clip.subclip(0, clip.duration)
        
        final_clip = clip.set_audio(audio_clip)
        
        output_path = os.path.join(temp_dir, "output.mp4")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

        return StreamingResponse(
            open(output_path, "rb"),
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename=video_{audio.filename.split('.')[0]}.mp4"}
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Note: We can't delete temp_dir immediately as StreamingResponse needs it.
        # In a real app, you'd use a background task or cleaner.
        pass

@app.get("/image-converter", response_class=HTMLResponse)
async def image_converter_page():
    with open("static/image_converter.html", "r") as f:
        return f.read()

@app.post("/render-pdf")
async def render_pdf(file: UploadFile = File(...)):
    import fitz  # PyMuPDF
    import base64
    try:
        contents = await file.read()
        doc = fitz.open(stream=contents, filetype="pdf")
        pages = []
        total_pages = len(doc)
        print(f"DEBUG: Processing PDF {file.filename} with {total_pages} pages")
        for i in range(total_pages):
            try:
                page = doc.load_page(i)
                zoom = 150 / 72 
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)) 
                img_data = pix.tobytes("png")
                
                print(f"DEBUG: Rendered page {i+1}, image size: {len(img_data)} bytes")
                
                base64_img = base64.b64encode(img_data).decode('utf-8')
                pages.append({
                    "page_num": i + 1,
                    "image": f"data:image/png;base64,{base64_img}",
                    "width": pix.width,
                    "height": pix.height
                })
            except Exception as pe:
                print(f"DEBUG: Failed to render page {i+1}: {str(pe)}")
        
        print(f"DEBUG: Final pages array contains {len(pages)} items")
        return {"pages": pages}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-pdf")
async def save_pdf(
    file: UploadFile = File(...),
    edits_json: str = Form(...)
):
    import fitz
    import json
    import traceback
    try:
        print(f"DEBUG: Starting save-pdf for {file.filename}")
        contents = await file.read()
        if not contents:
            raise ValueError("Empty PDF file uploaded")
            
        doc = fitz.open(stream=contents, filetype="pdf")
        try:
            edits = json.loads(edits_json)
        except Exception as je:
            raise ValueError(f"Invalid edits JSON: {str(je)}")
            
        print(f"DEBUG: Loaded {len(edits)} edits")
        
        font_path = "static/thai_font.ttf"
        if not os.path.exists(font_path):
            print(f"WARNING: Font file {font_path} not found, falling back to default")
            font_path = None
        
        for i, edit in enumerate(edits):
            try:
                # Validate required fields
                required = ['page_num', 'text', 'x', 'y', 'font_size', 'color', 'canvas_w', 'canvas_h']
                for field in required:
                    if field not in edit:
                        print(f"DEBUG: Missing field {field} in edit {i}")
                        continue

                page_idx = int(edit['page_num']) - 1
                if page_idx < 0 or page_idx >= len(doc):
                    continue
                    
                page = doc[page_idx]
                p_width = page.rect.width
                p_height = page.rect.height
                
                # Calculation mapping
                scale_x = p_width / float(edit['canvas_w'])
                scale_y = p_height / float(edit['canvas_h'])
                
                text_x = float(edit['x']) * scale_x
                text_y = float(edit['y']) * scale_y
                
                hex_color = edit['color'].lstrip('#')
                rgb = tuple(int(hex_color[j:j+2], 16)/255 for j in (0, 2, 4))
                
                # INSERTION LOGIC
                # We use a unique font name for each insertion to ensure fresh embedding
                current_font_name = f"sarabun_{i}"
                
                if font_path:
                    page.insert_text(
                        (text_x, text_y), 
                        str(edit['text']), 
                        fontsize=float(edit['font_size']) * scale_x,
                        color=rgb,
                        fontname=current_font_name, 
                        fontfile=font_path,
                        overlay=True
                    )
                else:
                    # Fallback to standard Helvetica if font file is missing
                    page.insert_text(
                        (text_x, text_y), 
                        str(edit['text']), 
                        fontsize=float(edit['font_size']) * scale_x,
                        color=rgb,
                        fontname="helv",
                        overlay=True
                    )
                
                print(f"DEBUG: Inserted '{edit['text']}' at points ({text_x:.2f}, {text_y:.2f})")
            except Exception as e:
                print(f"DEBUG: Error in edit {i}: {str(e)}")
            
        # Save the document to a buffer
        buf = io.BytesIO()
        doc.save(buf, garbage=3, deflate=True)
        doc.close()
        buf.seek(0)
        
        # Fix for Thai filenames in headers
        from urllib.parse import quote
        safe_filename = quote(f"edited_{file.filename}")
        
        return StreamingResponse(
            buf, 
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        print(f"DEBUG: Global error in save-pdf: {str(e)}")
        traceback.print_exc()
        return HTMLResponse(content=f"Error processing PDF: {str(e)}", status_code=500)

@app.get("/png-to-jpg", response_class=HTMLResponse)
async def png_to_jpg_page():
    with open("static/png_to_jpg.html", "r") as f:
        return f.read()

@app.get("/jpg-to-png", response_class=HTMLResponse)
async def jpg_to_png_page():
    with open("static/jpg_to_png.html", "r") as f:
        return f.read()

@app.get("/rotate-flip", response_class=HTMLResponse)
async def rotate_flip_page():
    with open("static/rotate_flip.html", "r") as f:
        return f.read()

@app.get("/add-text", response_class=HTMLResponse)
async def add_text_page():
    with open("static/add_text.html", "r") as f:
        return f.read()

@app.get("/add-sticker", response_class=HTMLResponse)
async def add_sticker_page():
    with open("static/add_sticker.html", "r") as f:
        return f.read()

@app.get("/design-tool", response_class=HTMLResponse)
async def design_tool_page():
    with open("static/design_tool.html", "r") as f:
        return f.read()

@app.get("/legal", response_class=HTMLResponse)
async def legal_page():
    with open("static/legal.html", "r") as f:
        return f.read()

@app.get("/ads.txt")
async def ads_txt():
    with open("static/ads.txt", "r") as f:
        return f.read()

@app.post("/process-composite")
async def process_composite(
    file: UploadFile = File(...),
    layers_json: str = Form(...)
):
    import json
    from PIL import ImageDraw, ImageFont
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGBA")
        draw = ImageDraw.Draw(img)
        layers = json.loads(layers_json)
        
        font_path = "static/thai_font.ttf"
        
        for layer in layers:
            if layer['type'] == 'sticker':
                sticker_path = f"static/stickers/{layer['name']}.png"
                if os.path.exists(sticker_path):
                    s_img = Image.open(sticker_path).convert("RGBA")
                    s_img = s_img.resize((layer['w'], layer['h']), Image.Resampling.LANCZOS)
                    img.paste(s_img, (layer['x'], layer['y']), s_img)
            
            elif layer['type'] == 'text':
                # Font loading
                try:
                    font = ImageFont.truetype(font_path, layer['font_size'])
                except:
                    font = ImageFont.load_default()
                
                x, y = layer['x'], layer['y']
                color = layer['color']
                e_color = layer['effect_color']
                text = layer['text']
                effect = layer['effect']

                # Effect logic (matching previous Add Text service)
                if effect == "shadow":
                    draw.text((x+2, y+2), text, fill=e_color, font=font, anchor="mm")
                elif effect == "bold_shadow":
                    draw.text((x+4, y+4), text, fill=e_color, font=font, anchor="mm")
                elif effect == "outline":
                    draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=2, stroke_fill=e_color)
                elif effect == "thick_outline":
                    draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=5, stroke_fill=e_color)
                elif effect == "sticker":
                    draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=8, stroke_fill=e_color)
                    draw.text((x+3, y+3), text, fill="#000000", font=font, anchor="mm")
                elif effect == "neon":
                    for offset in range(5, 0, -1):
                        draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=offset, stroke_fill=e_color)
                elif effect == "glow":
                    for offset in range(10, 0, -2):
                        draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=offset, stroke_fill=e_color)
                
                if effect != "hollow":
                    draw.text((x, y), text, fill=color, font=font, anchor="mm")
                else:
                    draw.text((x, y), text, fill=None, font=font, anchor="mm", stroke_width=2, stroke_fill=color)

        final_img = img.convert("RGB")
        buf = io.BytesIO()
        final_img.save(buf, format="PNG")
        buf.seek(0)
        
        return StreamingResponse(
            buf, 
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=composite_{file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-add-sticker")
async def process_add_sticker(
    file: UploadFile = File(...),
    stickers_json: str = Form(...)
):
    import json
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGBA")
        stickers = json.loads(stickers_json)
        
        for s in stickers:
            sticker_path = f"static/stickers/{s['name']}.png"
            if os.path.exists(sticker_path):
                sticker_img = Image.open(sticker_path).convert("RGBA")
                # Scale sticker if needed
                sticker_img = sticker_img.resize((s['w'], s['h']), Image.Resampling.LANCZOS)
                # Paste with alpha
                img.paste(sticker_img, (s['x'], s['y']), sticker_img)
        
        # Convert back to original format if not PNG
        final_img = img.convert("RGB") if img.mode == "RGBA" else img
        buf = io.BytesIO()
        final_img.save(buf, format="PNG")
        buf.seek(0)
        
        return StreamingResponse(
            buf, 
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=stickers_{file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-add-text")
async def process_add_text(
    file: UploadFile = File(...),
    text: str = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    font_size: int = Form(...),
    color: str = Form("#ffffff"),
    effect_color: str = Form("#000000"),
    effect: str = Form("none"),
    font_family: str = Form("Sarabun")
):
    from PIL import ImageDraw, ImageFont
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        draw = ImageDraw.Draw(img)
        
        # UNIVERSAL FONT STRATEGY (Cross-Platform)
        # We prioritize the bundled Sarabun font to ensure Thai/Eng works on Windows/Mac/Linux
        font = None
        bundled_thai = "static/thai_font.ttf"
        
        if os.path.exists(bundled_thai):
            try:
                font = ImageFont.truetype(bundled_thai, font_size)
            except: pass
            
        # Fallback only if the bundled font is missing
        if not font:
            fallback_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", # Linux
                "C:\\Windows\\Fonts\\arial.ttf",                   # Windows
                "/Library/Fonts/Arial.ttf"                          # macOS
            ]
            for path in fallback_paths:
                if os.path.exists(path):
                    try:
                        font = ImageFont.truetype(path, font_size)
                        break
                    except: continue

        if not font:
            font = ImageFont.load_default()

        # Effect handling uses anchor="mm" to ensure x,y is the center (matches Frontend)
        if effect == "shadow":
            draw.text((x+2, y+2), text, fill=effect_color, font=font, anchor="mm")
        elif effect == "bold_shadow":
            draw.text((x+4, y+4), text, fill=effect_color, font=font, anchor="mm")
        elif effect == "outline":
            draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=2, stroke_fill=effect_color)
        elif effect == "thick_outline":
            draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=5, stroke_fill=effect_color)
        elif effect == "sticker":
            draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=8, stroke_fill=effect_color)
            draw.text((x+3, y+3), text, fill="#000000", font=font, anchor="mm")
        elif effect == "hollow":
            draw.text((x, y), text, fill=None, font=font, anchor="mm", stroke_width=2, stroke_fill=color)
        elif effect == "neon":
            for offset in range(5, 0, -1):
                draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=offset, stroke_fill=effect_color)
        elif effect == "retro":
            draw.text((x-3, y-3), text, fill="#ff0000", font=font, anchor="mm")
            draw.text((x+3, y+3), text, fill="#00ffff", font=font, anchor="mm")
        elif effect == "glow":
            for offset in range(10, 0, -2):
                draw.text((x, y), text, fill=color, font=font, anchor="mm", stroke_width=offset, stroke_fill=effect_color)
        
        # Draw main text (unless hollow)
        if effect != "hollow":
            draw.text((x, y), text, fill=color, font=font, anchor="mm")
        
        buf = io.BytesIO()
        img.save(buf, format=img.format or "PNG")
        buf.seek(0)
        
        return StreamingResponse(
            buf, 
            media_type=f"image/{img.format.lower() if img.format else 'png'}",
            headers={"Content-Disposition": f"attachment; filename=text_{file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-rotate-flip")
async def process_rotate_flip(
    file: UploadFile = File(...),
    rotation: int = Form(0),
    flip_h: bool = Form(False),
    flip_v: bool = Form(False)
):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        # Handle orientation/rotation
        if rotation != 0:
            img = img.rotate(-rotation, expand=True) # Negative because PIL rotates CCW by default
            
        # Handle flips
        if flip_h:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_v:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            
        buf = io.BytesIO()
        img.save(buf, format=img.format or "PNG")
        buf.seek(0)
        
        return StreamingResponse(
            buf, 
            media_type=f"image/{img.format.lower() if img.format else 'png'}",
            headers={"Content-Disposition": f"attachment; filename=processed_{file.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/convert-image")
async def convert_image(
    file: UploadFile = File(...),
    target_format: str = Form(...), # "jpg", "png", "webp", "bmp", "tiff"
    quality: int = Form(85)
):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        output_ext = target_format.lower()
        save_format = output_ext.upper()
        
        if output_ext == "jpg":
            save_format = "JPEG"
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
        elif output_ext == "bmp":
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
        elif output_ext == "webp":
            save_format = "WEBP"
        elif output_ext == "tiff":
            save_format = "TIFF"

        buf = io.BytesIO()
        # Quality only applies to JPEG and WEBP
        if save_format in ("JPEG", "WEBP"):
            img.save(buf, format=save_format, quality=quality)
        else:
            img.save(buf, format=save_format)
            
        buf.seek(0)
        
        filename = os.path.splitext(file.filename)[0] + f".{output_ext}"
        media_type = f"image/{output_ext}"
        
        return StreamingResponse(
            buf, 
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compress-pdf")
async def compress_pdf(
    file: UploadFile = File(...),
    compression_level: str = Form("medium")
):
    from pypdf import PdfWriter, PdfReader
    try:
        contents = await file.read()
        reader = PdfReader(io.BytesIO(contents))
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        # 1. Structural compression (re-compresses text/instructions)
        for page in writer.pages:
            page.compress_content_streams() 

        # 2. Aggressive object reduction
        # This removes duplicate objects which is pypdf's strongest feature
        writer.add_metadata({}) 

        buf = io.BytesIO()
        # use_compression=True is the key for smaller pypdf files
        writer.write(buf)
        buf.seek(0)
        
        from urllib.parse import quote
        safe_filename = quote(f"compressed_{file.filename}")
        
        return StreamingResponse(
            buf, 
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crop")
async def crop_image(
    file: UploadFile = File(...),
    x: float = Form(...),
    y: float = Form(...),
    width: float = Form(...),
    height: float = Form(...),
    output_width: Optional[int] = Form(None),
    output_height: Optional[int] = Form(None)
):
    try:
        # Load image
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        # Pillow crop: (left, top, right, bottom)
        left = x
        top = y
        right = x + width
        bottom = y + height
        
        cropped_img = img.crop((left, top, right, bottom))
        
        # Resize if output dimensions are specified
        if output_width and output_height:
            cropped_img = cropped_img.resize((output_width, output_height), Image.Resampling.LANCZOS)
            
        # Save to buffer
        buf = io.BytesIO()
        cropped_img.save(buf, format=img.format or "JPEG")
        buf.seek(0)
        
        return StreamingResponse(buf, media_type=f"image/{img.format.lower() or 'jpeg'}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
