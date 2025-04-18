document.addEventListener('DOMContentLoaded', function () {
    document.body.addEventListener('click', function (e) {

        if (e.target.classList.contains('tab-link')) {

            if (e.target.classList.contains('disabled')) {
                e.preventDefault();
                return;
            }

            e.preventDefault();
            const tabId = e.target.getAttribute('data-tab');
            const tabPane = document.getElementById(tabId);

            if (!tabPane) {

                console.error('Tab pane not found:', tabId);
                return;

            }

            // Deactivate all tabs
            document.querySelectorAll('.tab-link').forEach(l => l.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

            // Activate clicked tab
            e.target.classList.add('active');
            tabPane.classList.add('active');

            // Handle analysis tab content loading
            if (tabId === 'chart' && tabPane.getAttribute('data-loaded') === 'false') {

                showLoadingOverlay();

                fetch('/generate_plots')
                    .then(response => {

                        if (!response.ok) throw new Error('Network error');
                        return response.json();


                    })
                    .then(data => {

                        if (data.compatible_plots_error) {
                            tabPane.innerHTML = `<div class="alert alert-info">${data.compatible_plots_error}</div>`;
                            return;
                        }

                        if (data.error) {
                            tabPane.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                            return;
                        }

                        // Clear previous content
                        tabPane.innerHTML = '<div id="chart-container"></div>';

                        try {

                            Bokeh.embed.embed_item(data.chart, "chart-container");

                            // Add fallback notice if needed
                            if (data.is_fallback) {
                                const notice = document.createElement('div');
                                notice.className = 'fallback-notice';
                                notice.innerHTML = `<div class="notifications notifications-info">
                                                    This chart was generated using an automated fallback configuration
                                                    </div>`;
                                tabPane.appendChild(notice);
                            }

                            tabPane.setAttribute('data-loaded', 'true');

                        } catch (e) {

                            tabPane.innerHTML = `Error rendering plot: ${e.message}`;

                        }
                    })
                    .catch(error => {

                        tabPane.innerHTML = `Error loading plot: ${error.message}`;

                    })
                    .finally(() => {
                        hideLoadingOverlay();
                    });
            }
        }
    });
});