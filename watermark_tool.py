#!/usr/bin/env python3
"""
图片水印添加工具
使用示例: python watermark_tool.py /path/to/images --font_size 36 --color white --position bottom-right
"""

import os
import argparse
from PIL import Image, ImageDraw, ImageFont
import piexif
from datetime import datetime
import glob

def get_exif_date(image_path):
    """从图片EXIF中获取拍摄日期 """
    try:
        exif_dict = piexif.load(image_path)
        
        # 尝试从EXIF的DateTimeOriginal获取原始拍摄时间
        if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').strftime('%Y年%m月%d日')
        
        # 如果找不到原始时间，尝试DateTime
        if '0th' in exif_dict and piexif.ImageIFD.DateTime in exif_dict['0th']:
            date_str = exif_dict['0th'][piexif.ImageIFD.DateTime].decode('utf-8')
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S').strftime('%Y年%m月%d日')
            
    except Exception as e:
        print(f"无法读取 {image_path} 的EXIF信息: {e}")
    
    return None

def get_watermark_position(img_width, img_height, text_width, text_height, position):
    """根据位置参数计算水印坐标"""
    padding = 20  # 边距
    
    if position == 'top-left':
        return (padding, padding)
    elif position == 'top-right':
        return (img_width - text_width - padding, padding)
    elif position == 'bottom-left':
        return (padding, img_height - text_height - padding)
    elif position == 'bottom-right':
        return (img_width - text_width - padding, img_height - text_height - padding)
    elif position == 'center':
        return ((img_width - text_width) // 2, (img_height - text_height) // 2)
    elif position == 'top-center':
        return ((img_width - text_width) // 2, padding)
    elif position == 'bottom-center':
        return ((img_width - text_width) // 2, img_height - text_height - padding)
    else:  # 默认右下角
        return (img_width - text_width - padding, img_height - text_height - padding)

def add_watermark_to_image(image_path, output_path, font_size=36, color='white', position='bottom-right'):
    """为单张图片添加水印"""
    try:
        # 打开图片
        with Image.open(image_path) as img:
            # 转换为RGB模式（确保兼容性）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 创建绘图对象
            draw = ImageDraw.Draw(img)
            
            # 获取拍摄日期
            watermark_text = get_exif_date(image_path)
            if not watermark_text:
                watermark_text = datetime.now().strftime('%Y年%m月%d日')
                print(f"使用当前日期作为 {os.path.basename(image_path)} 的水印")
            
            # 创建字体（使用默认字体，可根据需要修改）
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                        print("使用默认字体，建议安装arial字体以获得更好效果")
            
            # 获取文本尺寸
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 计算水印位置
            x, y = get_watermark_position(img.width, img.height, text_width, text_height, position)
            
            # 添加文本阴影效果（可选）
            shadow_color = 'black' if color == 'white' else 'black'
            draw.text((x+2, y+2), watermark_text, font=font, fill=shadow_color)
            
            # 添加主文本
            draw.text((x, y), watermark_text, font=font, fill=color)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存图片
            img.save(output_path, quality=95)
            print(f"已处理: {os.path.basename(image_path)} -> {watermark_text}")
            
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='为图片添加拍摄日期')
    parser.add_argument('image_path', help='图片文件路径或目录路径')
    parser.add_argument('--font_size', type=int, default=36, help='字体大小（默认: 36）')
    parser.add_argument('--color', default='white', help='水印颜色（默认: white）')
    parser.add_argument('--position', default='bottom-right', 
                       choices=['top-left', 'top-center', 'top-right', 
                               'center', 'bottom-left', 'bottom-center', 'bottom-right'],
                       help='水印位置（默认: bottom-right）')
    
    args = parser.parse_args()
    
    # 检查输入路径是否存在
    if not os.path.exists(args.image_path):
        print(f"错误: 路径 {args.image_path} 不存在")
        return
    
    # 确定是文件还是目录
    if os.path.isfile(args.image_path):
        image_files = [args.image_path]
        input_dir = os.path.dirname(args.image_path) or '.'
    else:
        input_dir = args.image_path
        # 支持常见图片格式
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.bmp', '*.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(input_dir, ext)))
            image_files.extend(glob.glob(os.path.join(input_dir, ext.upper())))
    
    if not image_files:
        print(f"在目录 {input_dir} 中未找到图片文件")
        return
    
    # 创建输出目录
    output_dir = os.path.join(input_dir, f"{os.path.basename(input_dir)}_watermark")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"开始处理 {len(image_files)} 张图片...")
    print(f"输出目录: {output_dir}")
    print(f"水印设置: 字体大小{args.font_size}, 颜色{args.color}, 位置{args.position}")
    print("-" * 50)
    
    # 处理每张图片
    for image_file in image_files:
        filename = os.path.basename(image_file)
        output_path = os.path.join(output_dir, filename)
        add_watermark_to_image(image_file, output_path, args.font_size, args.color, args.position)
    
    print("-" * 50)
    print(f"处理完成！所有图片已保存到: {output_dir}")

if __name__ == "__main__":
    main()