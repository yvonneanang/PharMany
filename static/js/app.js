function submitData() {
    // Get data from the input boxes
    const word1 = document.getElementById('searchBox1').value;
    const word2 = document.getElementById('searchBox2').value;

    // Make an AJAX request to send data to the Flask backend
    d3.json('/get_data', {
        method: 'POST',
        body: JSON.stringify({ words: [word1, word2] }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(function (data) {
        // Uncomment the following lines if you want to use D3.js to read the CSV data directly
         //d3.csv('/download_csv').then(function (data) {
         //    console.log(data);
        //     // Your D3.js code for visualization using the CSV data
         //});
    });
}
