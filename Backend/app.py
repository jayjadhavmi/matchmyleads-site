from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from io import BytesIO
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def standardize_columns(df):
    """Convert column names to lowercase and strip whitespace."""
    df.columns = df.columns.str.strip().str.lower()
    return df

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-columns', methods=['POST'])
def get_columns():
    try:
        # Check if files were uploaded
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({'error': 'Both files are required'}), 400
            
        file1 = request.files['file1']
        file2 = request.files['file2']
        
        # Check if filenames are empty
        if file1.filename == '' or file2.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Read Excel files
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            # Standardize column names
            df1.columns = df1.columns.str.strip().str.lower()
            df2.columns = df2.columns.str.strip().str.lower()
            
            # Return column names
            return jsonify({
                'user_columns': df2.columns.tolist(),
                'sfdc_columns': df1.columns.tolist()
            })
        except Exception as e:
            return jsonify({'error': f'Error reading Excel files: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in get-columns: {str(e)}")
        return jsonify({'error': f'Failed to process request: {str(e)}'}), 500

@app.route('/match', methods=['POST'])
def match_files():
    try:
        # Check if files were uploaded
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({'error': 'Both files are required'}), 400
            
        sfdc = request.files['file1']
        user = request.files['file2']
        match_column_input = request.form.get('match_column_input', '').strip().lower()
        match_column_sfdc = request.form.get('match_column_sfdc', '').strip().lower()
        return_columns = request.form.getlist('return_columns[]')
        
        # Ensure return_columns is a list
        if not isinstance(return_columns, list):
            return_columns = [return_columns]
        
        # Read Excel files
        try:
            sfdc_df = pd.read_excel(sfdc)
            user_df = pd.read_excel(user)
            
            # Standardize column names
            sfdc_df.columns = sfdc_df.columns.str.strip().str.lower()
            user_df.columns = user_df.columns.str.strip().str.lower()
            
            # Check if specified columns exist
            if match_column_sfdc not in sfdc_df.columns:
                return jsonify({'error': f"Column '{match_column_sfdc}' not found in SFDC file"}), 400
                
            if match_column_input not in user_df.columns:
                return jsonify({'error': f"Column '{match_column_input}' not found in Input file"}), 400
            
            # Create results dataframe
            results = []
            
            # Convert values to strings for matching
            sfdc_df[match_column_sfdc] = sfdc_df[match_column_sfdc].astype(str).str.strip().str.lower()
            user_df[match_column_input] = user_df[match_column_input].astype(str).str.strip().str.lower()
            
            # Simple exact matching
            for _, input_row in user_df.iterrows():
                input_value = input_row[match_column_input]
                row_data = {'Input Value': input_value}
                
                # Find matches in SFDC dataframe
                matches = sfdc_df[sfdc_df[match_column_sfdc] == input_value]
                
                if not matches.empty:
                    # Get the first match
                    match = matches.iloc[0]
                    row_data['Matched'] = 'Yes'
                    
                    # Add requested return columns
                    for col in return_columns:
                        if col in sfdc_df.columns:
                            row_data[col] = match[col]
                else:
                    row_data['Matched'] = 'No'
                    
                    # Add empty values for return columns
                    for col in return_columns:
                        if col in sfdc_df.columns:
                            row_data[col] = ''
                
                results.append(row_data)
            
            # Create output Excel file
            output_df = pd.DataFrame(results)
            output = BytesIO()
            output_df.to_excel(output, index=False)
            output.seek(0)
            
            return send_file(
                output,
                as_attachment=True,
                download_name='matched_results.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        except Exception as e:
            return jsonify({'error': f'Error processing Excel files: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in match: {str(e)}")
        return jsonify({'error': f'Failed to process request: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)