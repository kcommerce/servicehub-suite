let cropper;
const image = document.getElementById('image');
const imageUpload = document.getElementById('imageUpload');
const downloadBtn = document.getElementById('downloadBtn');
const placeholder = document.querySelector('.placeholder-text');
const presetBtns = document.querySelectorAll('.preset-btn');

const cropBtn = document.getElementById('cropBtn');
const previewSection = document.getElementById('preview-section');
const previewImage = document.getElementById('preview-image');
const closePreview = document.getElementById('closePreview');

let selectedFile = null;
let currentW = null;
let currentH = null;

imageUpload.addEventListener('change', (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
        selectedFile = files[0];
        const reader = new FileReader();
        reader.onload = (event) => {
            image.src = event.target.result;
            if (cropper) {
                cropper.destroy();
            }
            placeholder.style.display = 'none';
            initCropper();
            downloadBtn.disabled = false;
            cropBtn.disabled = false;
        };
        reader.readAsDataURL(selectedFile);
    }
});

function initCropper() {
    cropper = new Cropper(image, {
        viewMode: 1,
        dragMode: 'move',
        autoCropArea: 0.8,
        restore: false,
        guides: true,
        center: true,
        highlight: false,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
    });
}

closePreview.addEventListener('click', () => {
    previewSection.classList.add('hidden');
});

presetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Toggle active class
        presetBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const ratio = parseFloat(btn.dataset.ratio);
        currentW = btn.dataset.w ? parseInt(btn.dataset.w) : null;
        currentH = btn.dataset.h ? parseInt(btn.dataset.h) : null;

        if (cropper) {
            cropper.setAspectRatio(isNaN(ratio) ? 0 : ratio);
        }
    });
});

async function performCrop() {
    if (!cropper || !selectedFile) return null;

    const cropData = cropper.getData(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('x', cropData.x);
    formData.append('y', cropData.y);
    formData.append('width', cropData.width);
    formData.append('height', cropData.height);
    
    if (currentW && currentH) {
        formData.append('output_width', currentW);
        formData.append('output_height', currentH);
    }

    try {
        const response = await fetch('/crop', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            return await response.blob();
        }
        return null;
    } catch (error) {
        console.error(error);
        return null;
    }
}

cropBtn.addEventListener('click', async () => {
    cropBtn.textContent = '⏳ Processing...';
    cropBtn.disabled = true;

    const blob = await performCrop();
    if (blob) {
        const url = window.URL.createObjectURL(blob);
        previewImage.src = url;
        previewSection.classList.remove('hidden');
    } else {
        alert('Error cropping image');
    }

    cropBtn.textContent = '✨ Apply Crop';
    cropBtn.disabled = false;
});

downloadBtn.addEventListener('click', async () => {
    downloadBtn.textContent = '⏳ Processing...';
    downloadBtn.disabled = true;

    const blob = await performCrop();
    if (blob) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cropped_${selectedFile.name}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } else {
        alert('Error cropping image');
    }

    downloadBtn.textContent = '🚀 Download Crop';
    downloadBtn.disabled = false;
});
