'use client';

import React, { useState, useCallback } from 'react';
import Cropper from 'react-easy-crop';
import { X, Crop as CropIcon, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './ui/button';

interface Point {
  x: number;
  y: number;
}

interface Area {
  width: number;
  height: number;
  x: number;
  y: number;
}

interface AvatarCropperModalProps {
  isOpen: boolean;
  imageSrc: string;
  onClose: () => void;
  onCropCompleteAction: (croppedBlob: Blob) => Promise<void>;
}

export function AvatarCropperModal({ isOpen, imageSrc, onClose, onCropCompleteAction }: AvatarCropperModalProps) {
  const [crop, setCrop] = useState<Point>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const onCropComplete = useCallback((croppedArea: Area, croppedAreaPx: Area) => {
    setCroppedAreaPixels(croppedAreaPx);
  }, []);

  const createCrop = async () => {
    if (!croppedAreaPixels || !imageSrc) return;
    setIsProcessing(true);

    try {
      const croppedImage = await getCroppedImg(imageSrc, croppedAreaPixels);
      await onCropCompleteAction(croppedImage);
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-5 bg-black/80 backdrop-blur-md animate-[fadeIn_0.2s_ease-out]">
      <div className="w-full max-w-[500px] bg-[#0e131f] border border-indigo-500/25 rounded-2xl shadow-2xl p-6 relative flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-2 rounded-full transition-colors z-10 bg-black/20"
        >
          <X size={20} />
        </button>

        <div className="text-center mb-4">
          <h2 className="text-xl font-bold tracking-tight mb-1 flex items-center justify-center gap-2">
            <CropIcon size={20} className="text-indigo-400" />
            Position and Size
          </h2>
          <p className="text-slate-400 text-sm">Drag to reposition, or use controls</p>
        </div>

        <div className="relative w-full h-[300px] bg-black/50 rounded-xl overflow-hidden mb-6 border border-white/10">
          <Cropper
            image={imageSrc}
            crop={crop}
            zoom={zoom}
            aspect={1}
            cropShape="round"
            showGrid={false}
            onCropChange={setCrop}
            onCropComplete={onCropComplete}
            onZoomChange={setZoom}
          />
        </div>

        <div className="mb-6 px-2">
          <label className="block text-xs text-slate-400 font-medium mb-2 text-center">Zoom Level</label>
          <input
            type="range"
            value={zoom}
            min={1}
            max={3}
            step={0.1}
            aria-labelledby="Zoom"
            onChange={(e) => setZoom(Number(e.target.value))}
            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
        </div>

        <div className="flex flex-col items-center justify-center mb-6">
          <label className="block text-xs text-slate-400 font-medium mb-2">Fine Tune Position</label>
          <div className="grid grid-cols-3 gap-1">
            <div />
            <Button variant="secondary" className="!p-2" onClick={() => setCrop(c => ({ ...c, y: c.y - 10 }))}>
              <ChevronUp size={18} />
            </Button>
            <div />
            <Button variant="secondary" className="!p-2" onClick={() => setCrop(c => ({ ...c, x: c.x - 10 }))}>
              <ChevronLeft size={18} />
            </Button>
            <Button variant="secondary" className="!p-2" onClick={() => setCrop(c => ({ ...c, y: c.y + 10 }))}>
              <ChevronDown size={18} />
            </Button>
            <Button variant="secondary" className="!p-2" onClick={() => setCrop(c => ({ ...c, x: c.x + 10 }))}>
              <ChevronRight size={18} />
            </Button>
          </div>
        </div>

        <div className="flex gap-3 mt-auto">
          <Button variant="secondary" className="flex-1" onClick={onClose} disabled={isProcessing}>
            Cancel
          </Button>
          <Button className="flex-1" onClick={createCrop} isLoading={isProcessing}>
            Apply Crop
          </Button>
        </div>
      </div>
    </div>
  );
}

// Utility function to extract the cropped area via Canvas
async function getCroppedImg(
  imageSrc: string,
  pixelCrop: Area
): Promise<Blob> {
  const image = await createImage(imageSrc);
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  if (!ctx) {
    throw new Error('No 2d context');
  }

  // Set canvas size to the cropped size (e.g. 256x256 max)
  const maxSize = 400;
  let finalWidth = pixelCrop.width;
  let finalHeight = pixelCrop.height;

  if (pixelCrop.width > maxSize) {
    finalWidth = maxSize;
    finalHeight = maxSize;
  }

  canvas.width = finalWidth;
  canvas.height = finalHeight;

  ctx.drawImage(
    image,
    pixelCrop.x,
    pixelCrop.y,
    pixelCrop.width,
    pixelCrop.height,
    0,
    0,
    finalWidth,
    finalHeight
  );

  return new Promise((resolve, reject) => {
    canvas.toBlob((file) => {
      if (file) resolve(file);
      else reject(new Error('Canvas is empty'));
    }, 'image/webp', 0.95);
  });
}

function createImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener('load', () => resolve(image));
    image.addEventListener('error', (error) => reject(error));
    image.src = url;
  });
}
