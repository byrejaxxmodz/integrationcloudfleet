        // ---- AUTO QUOTA LOGIC ----
        async function updateQuota() {
            const clienteSelect = document.getElementById('selCliente');
            const clienteName = clienteSelect.options[clienteSelect.selectedIndex]?.text || "";
            
            const sedeSelect = document.getElementById('selSede');
            const sedeName = sedeSelect.options[sedeSelect.selectedIndex]?.text || "";
            
            const fechaVal = document.getElementById('selFecha').value;
            const quotaInput = document.getElementById('selQuota');

            if (clienteName && sedeName && fechaVal) {
                // If sede is "Todas las Sedes" (value=""), do nothing or assume manual
                if (!sedeSelect.value) return;

                try {
                    const params = new URLSearchParams({
                        cliente: clienteName,
                        sede: sedeName,
                        fecha: fechaVal
                    });
                    const res = await fetch(`${API_BASE}/api/quota?${params}`);
                    if (res.ok) {
                        const data = await res.json();
                        if (data.quota > 0) {
                            quotaInput.value = data.quota;
                            // Visual feedback
                            quotaInput.classList.add("bg-emerald-900", "text-emerald-100");
                            setTimeout(() => {
                                quotaInput.classList.remove("bg-emerald-900", "text-emerald-100");
                            }, 500);
                        } else {
                            // If 0, let user decide (maybe keep current or set to 1)
                            // quotaInput.value = 1; 
                        }
                    }
                } catch (e) {
                    console.error("Error fetching quota:", e);
                }
            }
        }

        // Attach listeners
        document.getElementById('selCliente').addEventListener('change', updateQuota);
        document.getElementById('selSede').addEventListener('change', updateQuota); // Sede change triggers cargaSedes logic, might need delay or callback
        document.getElementById('selFecha').addEventListener('change', updateQuota);
        
        // Also trigger when Sede is populated fully? 
        // We'll hook into the end of cargarSedes
