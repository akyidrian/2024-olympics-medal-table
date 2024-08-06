document.addEventListener('DOMContentLoaded', initializeTableSorting);

function initializeTableSorting() {
    const table = document.getElementsByTagName('table')[0];
    const headers = table.querySelectorAll('th');
    const tbody = table.querySelector('tbody');
    let currentSortColumn = null;
    let currentSortDirection = '';

    const defaultSortDirections = {
        0: 'asc', // Rank
        1: 'asc', // Country
        2: 'desc', // Gold
        3: 'desc', // Silver
        4: 'desc', // Bronze
        5: 'desc', // Total
        6: 'asc', // Population
        7: 'asc'  // Population per Medal
    };

    headers.forEach((header, index) => {
        header.addEventListener('click', () => {
        sortTable(index);
        });
    });

    function sortTable(column) {
        const currentDirection = currentSortColumn === column ? currentSortDirection : null;
        const defaultDirection = defaultSortDirections[column];

        let direction;
        if (currentDirection === null) {
            direction = defaultDirection;
        } else if (currentDirection === 'asc') {
            direction = 'desc';
        } else {
            direction = 'asc';
        }

        const multiplier = direction === 'asc' ? 1 : -1;
        const rows = Array.from(tbody.querySelectorAll('tr'));

        const sortedRows = rows.sort((rowA, rowB) => {
            let cellA = rowA.querySelectorAll('td')[column].textContent.trim();
            let cellB = rowB.querySelectorAll('td')[column].textContent.trim();

            // Check if the cell contains a number with commas and / or decimal places
            if (cellA.match(/^\d{1,3}(,\d{3})*(\.\d+)?$/) && cellB.match(/^\d{1,3}(,\d{3})*(\.\d+)?$/)) {
                cellA = parseFloat(cellA.replace(/,/g, ''));
                cellB = parseFloat(cellB.replace(/,/g, ''));
            }

            return cellA > cellB ? multiplier : cellA < cellB ? -multiplier : 0;
        });

        // Remove all existing rows from the table body
        while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
        }

        // Append sorted rows to the table body
        tbody.append(...sortedRows);

        // Update header classes
        headers.forEach((header, index) => {
            header.classList.remove('asc', 'desc');
            if (index === column) {
                header.classList.add(direction);
            }
        });

        // Update current sort state
        currentSortColumn = column;
        currentSortDirection = direction;
    }
}
