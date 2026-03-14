# ThaiEdit Pro 🚀

ThaiEdit Pro is a modern, high-performance web-based multi-service portal designed for media processing and document management. It provides a suite of essential tools for image editing, PDF manipulation, and file conversion—all within a single, intuitive interface.

**GitHub Repository:** [https://github.com/kcommerce/servicehub-suite](https://github.com/kcommerce/servicehub-suite)

## 🛠 Features

### 🎨 Design & Image Tools
*   **Design Tool:** A powerful layered editor combining multi-text and sticker support. Add 60+ 3D emojis and custom text with professional effects (Shadow, Outline, Neon).
*   **Crop Master:** Intelligent image cropping with 18+ presets including Social Media (IG, FB, YT, X) and ID/Passport standards (US, EU).
*   **Rotate & Flip:** Instant orientation adjustments with a live preview.
*   **Background Remover:** (Expandable) AI-powered subject isolation.

### 📄 PDF Management
*   **Edit PDF:** View and annotate multi-page PDFs. Add draggable text with support for Thai/Latin characters and interactive resizing handles.
*   **PDF Compressor:** Reduce file sizes while maintaining document integrity.

### 🔄 Conversion Suite
*   **PNG ➡️ JPG:** Fast conversion with adjustable quality sliders.
*   **JPG ➡️ PNG:** High-quality lossless conversion to PNG format.

## 🚀 Getting Started

### Prerequisites
*   Python 3.8+
*   Pip (Python package manager)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:kcommerce/servicehub-suite.git
    cd servicehub-suite
    ```

2.  **Set up Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Portal

Start the FastAPI server using Uvicorn:
```bash
python main.py
```
Once started, open your browser and navigate to:
`http://localhost:8000`

## 🌍 Cross-Platform Compatibility
ThaiEdit Pro is built to be truly OS-independent. By bundling essential assets like the **Sarabun** font, the suite guarantees a consistent **WYSIWYG (What You See Is What You Get)** experience across Windows, macOS, Linux, and Mobile devices.

## 🧰 Tech Stack
*   **Backend:** FastAPI (Python)
*   **Image Processing:** Pillow (PIL)
*   **PDF Engine:** PyMuPDF (fitz) & pypdf
*   **Frontend:** HTML5, CSS3 (Modern/Responsive), Vanilla JavaScript
*   **Interactive UI:** Cropper.js, Canvas API

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
