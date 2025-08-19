import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import textwrap
from PIL import Image, ImageDraw, ImageFont
import os

def parse_bingo_file(filename):
    """Parse the bingo.txt file and return a list of squares."""
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split by double newlines to get individual squares
    squares = [square.strip() for square in content.split('\n\n') if square.strip()]
    
    return squares

def format_square_text(square_text):
    """Format square text, handling two-line squares with different sizes."""
    lines = square_text.split('\n')
    
    if len(lines) == 1:
        # Single line - use much larger size
        return [(lines[0], 70)]
    elif len(lines) == 2:
        # Two lines - first line large, second line medium (but don't let +1 affect main text size)
        return [(lines[0], 65), (lines[1], 45)]
    else:
        # More than two lines - treat as single text block
        return [(square_text, 60)]

def wrap_text_pil(text, font, max_width):
    """Wrap text to fit within max_width using PIL, preserving word boundaries."""
    # Pre-process text to handle slashes as natural break points
    words = []
    for word in text.split():
        if '/' in word and len(word) > 6:  # Split words with slashes
            parts = word.split('/')
            for i, part in enumerate(parts):
                if i < len(parts) - 1:
                    words.append(part + '/')
                else:
                    words.append(part)
        else:
            words.append(word)
    
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                # Finish current line and start new line with this word
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Single word is too long - only break if absolutely necessary
                word_bbox = font.getbbox(word)
                word_width = word_bbox[2] - word_bbox[0]
                
                if word_width > max_width and len(word) > 12:  # Only break very long words
                    # Try to break at natural points (hyphens, etc.) first
                    if '-' in word:
                        parts = word.split('-')
                        for i, part in enumerate(parts):
                            if i < len(parts) - 1:
                                lines.append(part + '-')
                            else:
                                current_line = [part]
                    else:
                        # Break long word as last resort
                        for i in range(0, len(word), 8):
                            chunk = word[i:i+8]
                            if i + 8 < len(word):
                                lines.append(chunk + '-')
                            else:
                                current_line = [chunk]
                else:
                    # Word fits but was too long with previous words
                    current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def parse_bold_text(text):
    """Parse text for **bold** formatting and return segments with formatting info."""
    segments = []
    current_pos = 0
    
    while current_pos < len(text):
        # Find next bold marker
        bold_start = text.find('**', current_pos)
        
        if bold_start == -1:
            # No more bold text, add remaining as normal
            if current_pos < len(text):
                segments.append((text[current_pos:], False))
            break
        
        # Add text before bold marker as normal
        if bold_start > current_pos:
            segments.append((text[current_pos:bold_start], False))
        
        # Find closing bold marker
        bold_end = text.find('**', bold_start + 2)
        
        if bold_end == -1:
            # No closing marker, treat as normal text
            segments.append((text[bold_start:], False))
            break
        
        # Add bold text (without the ** markers)
        bold_text = text[bold_start + 2:bold_end]
        if bold_text:  # Only add if not empty
            segments.append((bold_text, True))
        
        current_pos = bold_end + 2
    
    return segments

def draw_text_with_bold(draw, text, x, y, font_normal, font_bold, color='black'):
    """Draw text with bold formatting support."""
    segments = parse_bold_text(text)
    current_x = x
    
    for segment_text, is_bold in segments:
        font = font_bold if is_bold else font_normal
        
        # Draw this segment
        draw.text((current_x, y), segment_text, fill=color, font=font)
        
        # Move x position for next segment
        bbox = font.getbbox(segment_text)
        current_x += bbox[2] - bbox[0]
    
    return current_x  # Return final x position

def wrap_text_with_bold(text, font_normal, font_bold, max_width):
    """Wrap text with bold formatting support and slash breaking."""
    segments = parse_bold_text(text)
    lines = []
    current_line = []
    current_line_width = 0
    
    for segment_text, is_bold in segments:
        font = font_bold if is_bold else font_normal
        
        # Pre-process segment to handle slashes as natural break points
        words = []
        for word in segment_text.split():
            if '/' in word and len(word) > 6:  # Split words with slashes
                parts = word.split('/')
                for i, part in enumerate(parts):
                    if i < len(parts) - 1:
                        words.append((part + '/', is_bold))
                    else:
                        words.append((part, is_bold))
            else:
                words.append((word, is_bold))
        
        for word, word_is_bold in words:
            # Calculate width of current line with this word
            test_words = [item[0] for item in current_line] + [word]
            test_text = ' '.join(test_words)
            test_font = font_bold if word_is_bold else font_normal
            bbox = test_font.getbbox(test_text)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width or not current_line:
                current_line.append((word, word_is_bold))
                current_line_width = test_width
            else:
                # Start new line
                lines.append(current_line)
                current_line = [(word, word_is_bold)]
                bbox = font.getbbox(word)
                current_line_width = bbox[2] - bbox[0]
    
    if current_line:
        lines.append(current_line)
    
    return lines

def create_bingo_card(squares):
    """Create a 5x5 bingo card with the first square as free space in center."""
    # Remove the free space from squares list for shuffling
    free_space = squares[0] if squares else "FREE"
    other_squares = squares[1:] if len(squares) > 1 else []
    
    # We need 24 squares (25 total - 1 free space)
    if len(other_squares) < 24:
        # If we don't have enough squares, repeat some
        while len(other_squares) < 24:
            other_squares.extend(squares[1:min(len(squares), 24)])
        other_squares = other_squares[:24]
    else:
        # If we have more than 24, randomly select 24
        other_squares = random.sample(other_squares, 24)
    
    # Shuffle the squares
    random.shuffle(other_squares)
    
    # Create 5x5 grid
    card = []
    square_index = 0
    
    for row in range(5):
        card_row = []
        for col in range(5):
            if row == 2 and col == 2:  # Center position (free space)
                card_row.append(free_space)
            else:
                card_row.append(other_squares[square_index])
                square_index += 1
        card.append(card_row)
    
    return card

def draw_bingo_on_template(card, template_path, output_path, bingo_start_y=950):
    """Draw a bingo card on the template image."""
    # Load template
    template = Image.open(template_path)
    template = template.convert('RGB')
    
    # Create drawing context
    draw = ImageDraw.Draw(template)
    
    # Calculate bingo card dimensions and position
    template_width, template_height = template.size
    card_width = int(template_width * 0.85)  # 85% of template width for good fit
    card_height = card_width  # Square card
    
    # Center horizontally
    card_x = (template_width - card_width) // 2
    card_y = bingo_start_y
    
    # Grid settings
    grid_size = 5
    cell_width = card_width // grid_size
    cell_height = card_height // grid_size
    
    # Try to load Goudy Old Style font, fallback to default
    try:
        font_large = ImageFont.truetype("C:/Windows/Fonts/GOUDOS.TTF", size=70)
        font_medium = ImageFont.truetype("C:/Windows/Fonts/GOUDOS.TTF", size=60)
        font_small = ImageFont.truetype("C:/Windows/Fonts/GOUDOS.TTF", size=50)
        # Try to load bold versions
        font_large_bold = ImageFont.truetype("C:/Windows/Fonts/GOUDOSB.TTF", size=70)
        font_medium_bold = ImageFont.truetype("C:/Windows/Fonts/GOUDOSB.TTF", size=60)
        font_small_bold = ImageFont.truetype("C:/Windows/Fonts/GOUDOSB.TTF", size=50)
    except:
        try:
            font_large = ImageFont.truetype("arial.ttf", size=70)
            font_medium = ImageFont.truetype("arial.ttf", size=60)
            font_small = ImageFont.truetype("arial.ttf", size=50)
            font_large_bold = ImageFont.truetype("arialbd.ttf", size=70)
            font_medium_bold = ImageFont.truetype("arialbd.ttf", size=60)
            font_small_bold = ImageFont.truetype("arialbd.ttf", size=50)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_large_bold = ImageFont.load_default()
            font_medium_bold = ImageFont.load_default()
            font_small_bold = ImageFont.load_default()
    
    # Draw grid and text
    for row in range(grid_size):
        for col in range(grid_size):
            # Calculate cell position
            cell_x = card_x + col * cell_width
            cell_y = card_y + row * cell_height
            
            # Draw cell border
            draw.rectangle([cell_x, cell_y, cell_x + cell_width, cell_y + cell_height], 
                         outline='black', width=3, fill='white')
            
            # Get square text
            square_text = card[row][col]
            formatted_text = format_square_text(square_text)
            
            # Calculate text position (center of cell)
            text_center_x = cell_x + cell_width // 2
            text_center_y = cell_y + cell_height // 2
            
            if len(formatted_text) == 1:
                # Single line or block of text
                text, font_size = formatted_text[0]
                font_normal = font_large if font_size >= 65 else font_medium if font_size >= 55 else font_small
                font_bold = font_large_bold if font_size >= 65 else font_medium_bold if font_size >= 55 else font_small_bold
                
                # Wrap text with bold support
                wrapped_lines = wrap_text_with_bold(text, font_normal, font_bold, cell_width - 40)
                
                # If text doesn't fit well, try smaller font
                if len(wrapped_lines) > 4:  # Too many lines
                    if font_normal == font_large:
                        font_normal = font_medium
                        font_bold = font_medium_bold
                        wrapped_lines = wrap_text_with_bold(text, font_normal, font_bold, cell_width - 40)
                    elif font_normal == font_medium:
                        font_normal = font_small
                        font_bold = font_small_bold
                        wrapped_lines = wrap_text_with_bold(text, font_normal, font_bold, cell_width - 40)
                
                # Calculate total text height and ensure it fits in cell
                line_height = font_normal.getbbox('Ay')[3] - font_normal.getbbox('Ay')[1] + 4
                total_height = len(wrapped_lines) * line_height
                
                # If text height exceeds cell height, reduce font size
                max_height = cell_height - 40
                if total_height > max_height:
                    if font_normal == font_large:
                        font_normal = font_medium
                        font_bold = font_medium_bold
                        wrapped_lines = wrap_text_with_bold(text, font_normal, font_bold, cell_width - 40)
                        line_height = font_normal.getbbox('Ay')[3] - font_normal.getbbox('Ay')[1] + 4
                        total_height = len(wrapped_lines) * line_height
                    elif font_normal == font_medium and total_height > max_height:
                        font_normal = font_small
                        font_bold = font_small_bold
                        wrapped_lines = wrap_text_with_bold(text, font_normal, font_bold, cell_width - 40)
                        line_height = font_normal.getbbox('Ay')[3] - font_normal.getbbox('Ay')[1] + 4
                        total_height = len(wrapped_lines) * line_height
                
                # Start from top of text block
                start_y = text_center_y - total_height // 2
                
                for i, line_segments in enumerate(wrapped_lines):
                    # Calculate line width to center it
                    line_width = 0
                    for word, is_bold in line_segments:
                        font = font_bold if is_bold else font_normal
                        bbox = font.getbbox(word + ' ')
                        line_width += bbox[2] - bbox[0]
                    
                    # Start x position for centered line
                    line_x = text_center_x - line_width // 2
                    line_y = start_y + i * line_height
                    
                    # Draw each segment in the line
                    current_x = line_x
                    for j, (word, is_bold) in enumerate(line_segments):
                        font = font_bold if is_bold else font_normal
                        word_text = word + (' ' if j < len(line_segments) - 1 else '')
                        
                        draw.text((current_x, line_y), word_text, fill='black', font=font)
                        
                        bbox = font.getbbox(word_text)
                        current_x += bbox[2] - bbox[0]
            
            else:
                # Two lines with different sizes
                line1, size1 = formatted_text[0]
                line2, size2 = formatted_text[1]
                
                font1_normal = font_large if size1 >= 65 else font_medium if size1 >= 55 else font_small
                font2_normal = font_large if size2 >= 65 else font_medium if size2 >= 55 else font_small
                font1_bold = font_large_bold if size1 >= 65 else font_medium_bold if size1 >= 55 else font_small_bold
                font2_bold = font_large_bold if size2 >= 65 else font_medium_bold if size2 >= 55 else font_small_bold
                
                # Wrap both lines with better padding and bold support
                wrapped_line1 = wrap_text_with_bold(line1, font1_normal, font1_bold, cell_width - 40)
                wrapped_line2 = wrap_text_with_bold(line2, font2_normal, font2_bold, cell_width - 40)
                
                # Auto-adjust font sizes ONLY if the main text (line1) doesn't fit
                # Don't let +1 text affect main text sizing
                if len(wrapped_line1) > 2:  # Too many lines for first text
                    if font1_normal == font_large:
                        font1_normal = font_medium
                        font1_bold = font_medium_bold
                        wrapped_line1 = wrap_text_with_bold(line1, font1_normal, font1_bold, cell_width - 40)
                    elif font1_normal == font_medium:
                        font1_normal = font_small
                        font1_bold = font_small_bold
                        wrapped_line1 = wrap_text_with_bold(line1, font1_normal, font1_bold, cell_width - 40)
                
                # For +1 text (line2), allow more aggressive sizing if needed without affecting line1
                if len(wrapped_line2) > 3:  # Allow more lines for +1 text before reducing
                    if font2_normal == font_large:
                        font2_normal = font_medium
                        font2_bold = font_medium_bold
                        wrapped_line2 = wrap_text_with_bold(line2, font2_normal, font2_bold, cell_width - 40)
                    elif font2_normal == font_medium:
                        font2_normal = font_small
                        font2_bold = font_small_bold
                        wrapped_line2 = wrap_text_with_bold(line2, font2_normal, font2_bold, cell_width - 40)
                
                # Calculate heights
                line1_height = font1_normal.getbbox('Ay')[3] - font1_normal.getbbox('Ay')[1] + 2
                line2_height = font2_normal.getbbox('Ay')[3] - font2_normal.getbbox('Ay')[1] + 2
                
                total_line1_height = len(wrapped_line1) * line1_height
                total_line2_height = len(wrapped_line2) * line2_height
                
                # Position +1 text (line2) at bottom of cell - always bottom aligned
                start_y2 = cell_y + cell_height - total_line2_height - 20  # Fixed distance from bottom
                
                # Try to center main text, but avoid overlap with +1 text
                min_gap = 20  # Minimum space between main text and +1 text
                ideal_center_y = text_center_y - total_line1_height // 2
                max_main_text_bottom = start_y2 - min_gap
                
                # If centered main text would overlap, move it up
                if ideal_center_y + total_line1_height > max_main_text_bottom:
                    start_y1 = max_main_text_bottom - total_line1_height
                else:
                    start_y1 = ideal_center_y
                
                # Ensure main text doesn't go above cell top
                min_y1 = cell_y + 20
                if start_y1 < min_y1:
                    start_y1 = min_y1
                
                for i, line_segments in enumerate(wrapped_line1):
                    # Calculate line width to center it
                    line_width = 0
                    for word, is_bold in line_segments:
                        font = font1_bold if is_bold else font1_normal
                        bbox = font.getbbox(word + ' ')
                        line_width += bbox[2] - bbox[0]
                    
                    line_x = text_center_x - line_width // 2
                    line_y = start_y1 + i * line1_height
                    
                    # Draw each segment in the line
                    current_x = line_x
                    for j, (word, is_bold) in enumerate(line_segments):
                        font = font1_bold if is_bold else font1_normal
                        word_text = word + (' ' if j < len(line_segments) - 1 else '')
                        
                        draw.text((current_x, line_y), word_text, fill='black', font=font)
                        
                        bbox = font.getbbox(word_text)
                        current_x += bbox[2] - bbox[0]
                
                for i, line_segments in enumerate(wrapped_line2):
                    # Calculate line width to center it
                    line_width = 0
                    for word, is_bold in line_segments:
                        font = font2_bold if is_bold else font2_normal
                        bbox = font.getbbox(word + ' ')
                        line_width += bbox[2] - bbox[0]
                    
                    line_x = text_center_x - line_width // 2
                    line_y = start_y2 + i * line2_height
                    
                    # Draw each segment in the line
                    current_x = line_x
                    for j, (word, is_bold) in enumerate(line_segments):
                        font = font2_bold if is_bold else font2_normal
                        word_text = word + (' ' if j < len(line_segments) - 1 else '')
                        
                        draw.text((current_x, line_y), word_text, fill='black', font=font)
                        
                        bbox = font.getbbox(word_text)
                        current_x += bbox[2] - bbox[0]
    
    # Save the final image
    template.save(output_path, 'PNG', quality=95, dpi=(300, 300))
    return output_path

def main():
    """Generate individual bingo cards on templates."""
    try:
        # Get number of cards from user with default of 12
        user_input = input("How many bingo cards would you like to generate? (default: 12): ").strip()
        if user_input == "":
            num_cards = 12
        else:
            try:
                num_cards = int(user_input)
                if num_cards <= 0:
                    print("Number of cards must be positive. Using default of 12.")
                    num_cards = 12
            except ValueError:
                print("Invalid input. Using default of 12.")
                num_cards = 12
        
        # Create finals directory if it doesn't exist
        os.makedirs('finals', exist_ok=True)
        
        # Parse the bingo file
        squares = parse_bingo_file('bingo.txt')
        print(f"Loaded {len(squares)} bingo squares")
        
        # Generate unique bingo cards
        for i in range(1, num_cards + 1):
            print(f"Generating bingo card {i}/{num_cards}...")
            
            # Create a unique bingo card
            card = create_bingo_card(squares)
            
            # Draw on template and save
            output_filename = f"finals/bingo_card_{i:02d}.png"
            draw_bingo_on_template(card, 'bingo.png', output_filename)
            
            print(f"Saved: {output_filename}")
        
        print(f"\nAll {num_cards} bingo cards generated successfully in the 'finals' folder!")
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
