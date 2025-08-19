from PIL import Image
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import glob

def create_bingo_pdf():
    """Create a PDF from all bingo cards in the finals folder."""
    
    # Get all bingo card files from finals folder
    finals_path = "finals"
    if not os.path.exists(finals_path):
        print("Error: 'finals' folder not found!")
        return
    
    # Find all bingo card PNG files
    card_files = glob.glob(os.path.join(finals_path, "bingo_card_*.png"))
    card_files.sort()  # Sort to ensure consistent order
    
    if not card_files:
        print("Error: No bingo card files found in finals folder!")
        return
    
    print(f"Found {len(card_files)} bingo cards to include in PDF")
    
    # Create PDF
    pdf_filename = "bingo_cards_printable.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    
    # Letter size dimensions in points (72 points = 1 inch)
    page_width, page_height = letter  # 612 x 792 points
    
    for i, card_file in enumerate(card_files):
        print(f"Adding card {i+1}/{len(card_files)}: {os.path.basename(card_file)}")
        
        try:
            # Open the image
            img = Image.open(card_file)
            
            # Calculate scaling to fit full page
            max_width = page_width
            max_height = page_height
            
            # Get image dimensions
            img_width, img_height = img.size
            
            # Calculate scale factor to fit the page while maintaining aspect ratio
            scale_x = max_width / img_width
            scale_y = max_height / img_height
            scale = min(scale_x, scale_y)
            
            # Calculate final dimensions
            final_width = img_width * scale
            final_height = img_height * scale
            
            # Calculate position to center the image
            x = (page_width - final_width) / 2
            y = (page_height - final_height) / 2
            
            # Add image to PDF
            c.drawImage(ImageReader(img), x, y, width=final_width, height=final_height)
            
            # Start new page for next card (except for the last one)
            if i < len(card_files) - 1:
                c.showPage()
                
        except Exception as e:
            print(f"Error processing {card_file}: {e}")
            continue
    
    # Save the PDF
    c.save()
    print(f"\nPDF created successfully: {pdf_filename}")
    print(f"The PDF contains {len(card_files)} bingo cards, one per page")
    print("Ready for printing on standard letter-size paper!")

def create_multiple_per_page_pdf():
    """Create a PDF with multiple cards per page for smaller printing."""
    
    # Get all bingo card files from finals folder
    finals_path = "finals"
    if not os.path.exists(finals_path):
        print("Error: 'finals' folder not found!")
        return
    
    # Find all bingo card PNG files
    card_files = glob.glob(os.path.join(finals_path, "bingo_card_*.png"))
    card_files.sort()
    
    if not card_files:
        print("Error: No bingo card files found in finals folder!")
        return
    
    print(f"Creating compact PDF with {len(card_files)} cards (4 per page)")
    
    # Create PDF
    pdf_filename = "bingo_cards_compact.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    
    # Letter size dimensions
    page_width, page_height = letter
    
    # Calculate positions for 2x2 grid
    margin = 20
    card_width = (page_width - 3 * margin) / 2
    card_height = (page_height - 3 * margin) / 2
    
    positions = [
        (margin, page_height - margin - card_height),  # Top left
        (margin + card_width + margin, page_height - margin - card_height),  # Top right
        (margin, page_height - margin - 2 * card_height - margin),  # Bottom left
        (margin + card_width + margin, page_height - margin - 2 * card_height - margin)  # Bottom right
    ]
    
    cards_on_page = 0
    page_num = 1
    
    for i, card_file in enumerate(card_files):
        try:
            # Open the image
            img = Image.open(card_file)
            
            # Get position for this card
            pos_x, pos_y = positions[cards_on_page]
            
            # Add image to PDF
            c.drawImage(ImageReader(img), pos_x, pos_y, width=card_width, height=card_height)
            
            # Add card label
            c.setFont("Helvetica", 8)
            card_label = f"Card {i+1:02d}"
            c.drawString(pos_x + 5, pos_y - 15, card_label)
            
            cards_on_page += 1
            
            # If we've filled the page or reached the last card, finish the page
            if cards_on_page >= 4 or i == len(card_files) - 1:
                # Add page number
                c.setFont("Helvetica", 10)
                page_text = f"Page {page_num}"
                text_width = c.stringWidth(page_text, "Helvetica", 10)
                c.drawString((page_width - text_width) / 2, 10, page_text)
                
                if i < len(card_files) - 1:
                    c.showPage()
                    page_num += 1
                cards_on_page = 0
                
        except Exception as e:
            print(f"Error processing {card_file}: {e}")
            continue
    
    c.save()
    print(f"\nCompact PDF created: {pdf_filename}")
    print(f"Contains {len(card_files)} cards with 4 cards per page")

def main():
    """Main function to create PDFs."""
    print("Bingo Card PDF Generator")
    print("=" * 30)
    
    while True:
        print("\nChoose PDF format:")
        print("1. One card per page (full size, best for playing)")
        print("2. Four cards per page (compact, good for overview)")
        print("3. Both formats")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            create_bingo_pdf()
            break
        elif choice == "2":
            create_multiple_per_page_pdf()
            break
        elif choice == "3":
            create_bingo_pdf()
            create_multiple_per_page_pdf()
            break
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
