document.addEventListener('DOMContentLoaded', function() {
    function updateTotal() {
        let total = 0;
        document.querySelectorAll('.dynamic-saleitem').forEach(function(row) {
            const qty = parseFloat(row.querySelector('[name$="-quantity"]').value) || 0;
            const price = parseFloat(row.querySelector('[name$="-price"]').value) || 0;
            total += qty * price;
        });
        document.querySelector('#id_total_price').value = total.toFixed(2);
    }

    document.querySelectorAll('input').forEach(function(input){
        input.addEventListener('input', updateTotal);
    });

    updateTotal();  // sahifa yuklanganda ham total chiqadi
});
