document.addEventListener('DOMContentLoaded', () => {
    const monthInputs = document.querySelectorAll('input[type="month"]');
    const tooltips = document.querySelectorAll('.tooltip');

    monthInputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.showPicker();
        });
    });

    tooltips.forEach(tooltip => {
        tooltip.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAllTooltips();
            tooltip.classList.add('active');
        });
    });

    document.addEventListener('click', () => {
        closeAllTooltips();
    });

    function closeAllTooltips() {
        tooltips.forEach(tooltip => {
            tooltip.classList.remove('active');
        });
    }
});
