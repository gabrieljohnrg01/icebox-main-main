            const RL_DATA = window.DYNAMIC_RL_DATA || {};

            /**
             * Shows the indicator and description info card below a readiness level select
             * when the user selects a level from the dropdown.
             */
            function showRLInfo(selectEl) {
                const rlType = selectEl.dataset.rlType; // e.g. 'TRL'
                const val = selectEl.value; // e.g. 'Level 3'
                const infoCardId = rlType.toLowerCase() + 'InfoCard';
                const infoCard = document.getElementById(infoCardId);

                if (!infoCard) return;

                // Parse level number from value
                const match = val.match(/Level\s+(\d+)/i);
                if (!match) {
                    infoCard.style.display = 'none';
                    infoCard.innerHTML = '';
                    return;
                }

                const levelNum = parseInt(match[1]);
                const data = RL_DATA[rlType] && RL_DATA[rlType][levelNum];

                if (!data) {
                    infoCard.style.display = 'none';
                    infoCard.innerHTML = '';
                    return;
                }

                // User requested to hide the info card entirely to save space
                infoCard.style.display = 'none';
                infoCard.innerHTML = '';
            }

            // ===== Custom Dropdown with Hover Tooltip Functions =====

            /** Build menu items for a custom dropdown from RL_DATA */
            function initRLDropdownMenu(dropdownEl) {
                const rlType = dropdownEl.dataset.rlType;
                const menu = dropdownEl.querySelector('.rl-dd-menu');
                if (!menu || menu.children.length > 0) return; // already built

                const data = RL_DATA[rlType];
                if (!data) return;

                const levels = Object.keys(data).sort((a,b) => parseInt(a) - parseInt(b));
                
                if (levels.length === 0) {
                    const opt = document.createElement('div');
                    opt.className = 'rl-dd-option';
                    opt.innerHTML = '<span class="rl-dd-opt-level" style="width: 100%; color: red;">No levels in DB!</span>';
                    menu.appendChild(opt);
                    return;
                }

                for (const lvlStr of levels) {
                    const d = data[lvlStr];
                    if (!d) continue;
                    const lvl = parseInt(lvlStr) || lvlStr;
                    const opt = document.createElement('div');
                    opt.className = 'rl-dd-option';
                    opt.dataset.value = `Level ${lvl}`;

                    opt.innerHTML = `
                        <span class="rl-dd-opt-level" style="width: 100%;">Level ${lvl}</span>
                        <div class="rl-dd-tooltip">
                            <div class="rl-tooltip-badge">${rlType} Level ${lvl}</div>
                            <div class="rl-tooltip-desc">${d.description}</div>
                        </div>
                    `;

                    // Position tooltip on hover
                    opt.addEventListener('mouseenter', function(e) {
                        const tooltip = this.querySelector('.rl-dd-tooltip');
                        if (!tooltip) return;
                        const rect = this.getBoundingClientRect();
                        const vw = window.innerWidth;

                        // Compensate for CSS backdrop-filter breaking position: fixed coordinates
                        tooltip.style.left = '0px';
                        tooltip.style.top = '0px';
                        // Force a layout recalculation to get the true offset of the containing block
                        const offsetRect = tooltip.getBoundingClientRect();
                        const offsetX = offsetRect.left;
                        const offsetY = offsetRect.top;

                        // Try placing to the right; if not enough space, place to the left
                        if (rect.right + 330 < vw) {
                            tooltip.style.left = (rect.right - offsetX + 8) + 'px';
                        } else {
                            tooltip.style.left = (rect.left - offsetX - 328) + 'px';
                        }
                        tooltip.style.top = Math.max(8 - offsetY, rect.top - offsetY - 20) + 'px';
                    });

                    // Click to select
                    opt.addEventListener('click', function(e) {
                        e.stopPropagation();
                        selectRLOption(dropdownEl, this.dataset.value);
                    });

                    menu.appendChild(opt);
                }
            }

            /** Toggle a custom dropdown open/closed */
            function toggleRLDropdown(triggerEl) {
                const dropdown = triggerEl.parentElement;
                const menu = dropdown.querySelector('.rl-dd-menu');
                const isOpen = menu.classList.contains('open');

                // Close all other open menus first
                document.querySelectorAll('.rl-dd-menu.open').forEach(m => {
                    m.classList.remove('open');
                    m.parentElement.querySelector('.rl-dd-trigger').classList.remove('open');
                });

                if (!isOpen) {
                    initRLDropdownMenu(dropdown); // lazy-build
                    menu.classList.add('open');
                    triggerEl.classList.add('open');

                    // Highlight the currently selected option
                    const currentVal = dropdown.querySelector('.rl-dd-label').textContent;
                    menu.querySelectorAll('.rl-dd-option').forEach(opt => {
                        opt.classList.toggle('selected', opt.dataset.value === currentVal);
                    });
                }
            }

            /** Select an option in the custom dropdown */
            function selectRLOption(dropdownEl, value) {
                const label = dropdownEl.querySelector('.rl-dd-label');
                const menu = dropdownEl.querySelector('.rl-dd-menu');
                const trigger = dropdownEl.querySelector('.rl-dd-trigger');
                const targetSelectId = dropdownEl.dataset.target;
                const targetSelect = document.getElementById(targetSelectId);

                label.textContent = value;
                menu.classList.remove('open');
                trigger.classList.remove('open');

                // Sync hidden select
                if (targetSelect) {
                    targetSelect.value = value;
                    // Fire change event for showRLInfo
                    targetSelect.dispatchEvent(new Event('change'));
                }

                // Also trigger showRLInfo
                showRLInfo(targetSelect);
            }

            /** Set the custom dropdown value without opening it */
            function setRLDropdownValue(dropdownEl, value) {
                const label = dropdownEl.querySelector('.rl-dd-label');
                if (label) label.textContent = value || dropdownEl.dataset.placeholder;
            }

            /** Show/hide a custom dropdown */
            function showRLDropdown(dropdownEl, show) {
                dropdownEl.style.display = show ? 'block' : 'none';
            }

            /** Enable/disable a custom dropdown */
            function setRLDropdownDisabled(dropdownEl, disabled) {
                const trigger = dropdownEl.querySelector('.rl-dd-trigger');
                if (disabled) {
                    trigger.classList.add('disabled');
                } else {
                    trigger.classList.remove('disabled');
                }
            }

            // Close dropdown menus when clicking outside
            document.addEventListener('click', function(e) {
                if (!e.target.closest('.rl-custom-dropdown')) {
                    document.querySelectorAll('.rl-dd-menu.open').forEach(m => {
                        m.classList.remove('open');
                        m.parentElement.querySelector('.rl-dd-trigger').classList.remove('open');
                    });
                }
            });

