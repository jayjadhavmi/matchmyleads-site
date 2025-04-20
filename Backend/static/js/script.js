document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const loadColumnsBtn = document.getElementById('load-columns-btn');
    const matchBtn = document.getElementById('match-btn');
    const uploadForm = document.getElementById('upload-form');
    const columnsSection = document.getElementById('columns-section');
    const loadingElement = document.getElementById('loading');
    const messageElement = document.getElementById('message');
    
    // Event listeners
    loadColumnsBtn.addEventListener('click', loadColumns);
    uploadForm.addEventListener('submit', matchFiles);
    
    // Show message function
    function showMessage(text, type) {
        messageElement.textContent = text;
        messageElement.className = 'message ' + type;
        
        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                messageElement.textContent = '';
                messageElement.className = 'message';
            }, 5000);
        }
    }
    
    // Show/hide loading
    function setLoading(isLoading) {
        if (isLoading) {
            loadingElement.style.display = 'flex';
        } else {
            loadingElement.style.display = 'none';
        }
    }
    
    // Load columns function
    async function loadColumns() {
        const file1 = document.getElementById('file1').files[0];
        const file2 = document.getElementById('file2').files[0];
        
        // Validate files
        if (!file1 || !file2) {
            showMessage('Please select both files', 'error');
            return;
        }
        
        setLoading(true);
        loadColumnsBtn.disabled = true;
        
        try {
            const formData = new FormData();
            formData.append('file1', file1);
            formData.append('file2', file2);
            
            const response = await fetch('/get-columns', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Populate dropdowns
                populateDropdowns(data);
                
                // Show columns section
                columnsSection.style.display = 'block';
                showMessage('Columns loaded successfully', 'success');
            } else {
                showMessage('Error: ' + (data.error || 'Failed to load columns'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('An error occurred while loading columns', 'error');
        } finally {
            setLoading(false);
            loadColumnsBtn.disabled = false;
        }
    }
    
    // Populate dropdowns with columns
    function populateDropdowns(data) {
        const inputSelect = document.getElementById('match_column_input');
        const sfdcSelect = document.getElementById('match_column_sfdc');
        const returnSelect = document.getElementById('return_columns');
        
        // Clear existing options
        inputSelect.innerHTML = '';
        sfdcSelect.innerHTML = '';
        returnSelect.innerHTML = '';
        
        // Add options for input file columns
        data.user_columns.forEach(column => {
            inputSelect.add(new Option(column, column));
        });
        
        // Add options for SFDC file columns
        data.sfdc_columns.forEach(column => {
            sfdcSelect.add(new Option(column, column));
            returnSelect.add(new Option(column, column));
        });
    }
    
    // Match files function
    async function matchFiles(event) {
        event.preventDefault();
        
        // Get form values
        const inputColumn = document.getElementById('match_column_input').value;
        const sfdcColumn = document.getElementById('match_column_sfdc').value;
        const returnColumns = [...document.getElementById('return_columns').selectedOptions].map(option => option.value);
        
        // Validate selections
        if (!inputColumn || !sfdcColumn || returnColumns.length === 0) {
            showMessage('Please select all required columns', 'error');
            return;
        }
        
        setLoading(true);
        matchBtn.disabled = true;
        
        try {
            const formData = new FormData(uploadForm);
            
            const response = await fetch('/match', {
                method: 'POST',
                body: formData
            });
            
            // Check if response is JSON (error) or file (success)
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                // Error response
                const errorData = await response.json();
                showMessage('Error: ' + (errorData.error || 'Failed to process files'), 'error');
            } else {
                // File response - trigger download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'matched_results.xlsx';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                showMessage('Matching completed successfully! File downloaded.', 'success');
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('An error occurred while matching files', 'error');
        } finally {
            setLoading(false);
            matchBtn.disabled = false;
        }
    }
});