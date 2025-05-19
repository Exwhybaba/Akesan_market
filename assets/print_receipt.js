// PDF receipt generation function for the market management system
window.generateReceiptPDF = function(receiptId) {
    // Get the receipt content
    const receiptContent = document.getElementById(receiptId || 'receipt-content');
    
    if (!receiptContent) {
        console.error('Receipt content not found');
        return;
    }
    
    // Create a clone of the receipt element to modify it for PDF generation
    const receiptClone = receiptContent.cloneNode(true);
    
    // Create a temporary container
    const tempContainer = document.createElement('div');
    tempContainer.style.width = '76mm';
    tempContainer.style.padding = '5mm';
    tempContainer.style.background = 'white';
    tempContainer.style.position = 'absolute';
    tempContainer.style.left = '-9999px';
    tempContainer.appendChild(receiptClone);
    
    // Add footer
    const footer = document.createElement('div');
    footer.innerHTML = `
        <div style="margin-top: 15px; text-align: center; font-size: 10px; border-top: 1px dashed #000; padding-top: 5px;">
            <p style="margin: 5px 0;">Thank you for your payment!</p>
            <p style="margin: 5px 0;">Oyo East Local Government Market Management</p>
        </div>
    `;
    tempContainer.appendChild(footer);
    
    // Add to document body temporarily
    document.body.appendChild(tempContainer);
    
    // Use html2canvas to capture the receipt as an image
    html2canvas(tempContainer, {
        scale: 2, // Higher scale for better quality
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
    }).then(canvas => {
        // Remove the temporary container
        document.body.removeChild(tempContainer);
        
        // Create PDF using jsPDF
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: [80, 210] // 80mm width (standard receipt width)
        });
        
        // Get the receipt date from the content if available
        let receiptDate = 'receipt';
        const dateElement = receiptContent.querySelector('.receipt-number');
        if (dateElement) {
            const dateMatch = dateElement.textContent.match(/\d{2}-\d{2}-\d{4}/);
            if (dateMatch) {
                receiptDate = dateMatch[0].replace(/\//g, '-');
            }
        }
        
        // Add the image to PDF
        const imgData = canvas.toDataURL('image/png');
        const imgWidth = 76; // 76mm width
        const imgHeight = canvas.height * imgWidth / canvas.width;
        
        pdf.addImage(imgData, 'PNG', 2, 2, imgWidth, imgHeight);
        
        // Download PDF
        pdf.save(`Market_${receiptDate}.pdf`);
    }).catch(err => {
        console.error('Error generating PDF:', err);
        alert('Error generating PDF. Please try again.');
    });
};

// Legacy print function (kept for compatibility)
window.printReceipt = function(receiptId) {
    window.generateReceiptPDF(receiptId);
};

// Register a global clientside callback for Dash
if (window.dash_clientside) {
    window.dash_clientside.print_receipt = {
        print_receipt: function(n_clicks) {
            if (n_clicks) {
                window.generateReceiptPDF('receipt-content');
                return null;
            }
            return window.dash_clientside.no_update;
        }
    };
} 