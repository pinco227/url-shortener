(function () {
    // Prevent delete without confirm
    const deleteButtons = document.querySelectorAll('.delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            if (!confirm("Are you sure you want to delete?")) {
                e.preventDefault();
                e.stopPropagation();
            }
        })
    })

	// Dismiss flash messages after 6 seconds
	const flashElement = document.getElementById('flash');

	if(flashElement) {
		setTimeout(() => {
			flashElement.remove();
		}, 6000);
	}
})();