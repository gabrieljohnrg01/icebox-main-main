            const RL_DATA = {
                TRL: {
                    1: {
                        indicator: "Basic principles observed",
                        description: "Published research that identifies the basic principles that underlie a technology.\nScientific research begins to be translated into more applied research and development."
                    },
                    2: {
                        indicator: "Technology concept and/or application formulated",
                        description: "The potential technology/product concept is defined and described.\nPractical applications can be defined/researched but are speculative and no proof or detailed analysis."
                    },
                    3: {
                        indicator: "Analytical and experimental proof-of-concept of critical function and/or characteristics",
                        description: "Active R&D is initiated to develop the technology/product further.\nAnalytical studies and laboratory-based or experimental studies are performed to physically validate that analytical predictions are correct."
                    },
                    4: {
                        indicator: "Technology validation in laboratory",
                        description: "Basic technological components are integrated to establish that they will work together.\nThis is relatively \u201Clow fidelity\u201D compared with the eventual system."
                    },
                    5: {
                        indicator: "Technology validation in relevant environment",
                        description: "Basic technological components integrated with reasonably realistic supporting elements so they can be tested in a simulated environment.\nFidelity of breadboard technology increases significantly."
                    },
                    6: {
                        indicator: "Technology demonstration in a relevant environment",
                        description: "Representative model or prototype system, tested in a relevant environment.\nRepresents a major step up and requires evidence of performance on full-scale, realistic problems."
                    },
                    7: {
                        indicator: "Technology prototype demonstration in an operational environment",
                        description: "Prototype near or at planned operational system.\nRequiring demonstration of an actual system prototype in an operational environment.\nCritical technological properties are measured against requirements."
                    },
                    8: {
                        indicator: "Actual Technology system completed and qualified through test and demonstration",
                        description: "Technology has been proven to work in its final form and under expected conditions.\nIn almost all cases, this TRL represents the end of true system development."
                    },
                    9: {
                        indicator: "Actual Technology system proven in operational environment",
                        description: "Actual application of the technology in its final form and under mission/operational conditions.\nTechnology is ready for commercial deployment."
                    }
                },
                CRL: {
                    1: {
                        indicator: "Hypothesizing on possible needs in market",
                        description: "Thinking that a possible need/problem or opportunity might exist in a market.\nNo clear hypotheses on who customers are and what problems are.\nLimited or non-existing knowledge of the market and customers/users."
                    },
                    2: {
                        indicator: "Identified specific needs in market",
                        description: "Some market research is performed, typically derived from secondary sources.\nBrief familiarity with the market, possible customers and their problems/needs.\nProduct/solution ideas may exist, but are not clear and typically speculative."
                    },
                    3: {
                        indicator: "First market feedback established",
                        description: "Initiated customer discovery with feedback from primary market research.\nA more developed understanding of possible customers and possible customer segments.\nA more clear problem hypothesis."
                    },
                    4: {
                        indicator: "Confirmed problem/needs from several customers or users",
                        description: "Contacts and feedback are established with several possible customers/users.\nThe problem and need (and its importance) is confirmed from multiple customers/users.\nCustomer segmentation in place, a primary product hypothesis is defined."
                    },
                    5: {
                        indicator: "Established interest for product and relations with target customers",
                        description: "General interest from customers/users for the product where the possible product/solution is confirmed to solve customers' problems.\nEstablished relationships with potential target customers, users or partners.\nDefined who the target customers/segments are to be focused on."
                    },
                    6: {
                        indicator: "Benefits of the product confirmed through partnerships or first customer testing",
                        description: "Testing of product by customers/users where the value and benefits of the product is confirmed.\nPartnerships formed with key stakeholders in value chain.\nInitiated structured business development/sales activities."
                    },
                    7: {
                        indicator: "Customers in extended product testing or first test sales",
                        description: "Customer agreements in place \u2013 first sales and/or test sales of product versions take place.\nCustomers and relevant stakeholders engaged in product qualifications/extended testing.\nRamp up of business development and sales efforts."
                    },
                    8: {
                        indicator: "First products sold and increased structured sales efforts",
                        description: "Customer qualifications are complete and initial products are sold to a few customers.\nPayment willingness confirmed from sufficient % of customers (product-market fit validated).\nThe real buyers/economic decision makers are identified."
                    },
                    9: {
                        indicator: "Widespread product sales that scale",
                        description: "Widespread product deployment, sales to several customers in a repeatable and scalable way.\nCustomer creation \u2013 company focuses on execution with growth of sales and efforts to build user/customer demand."
                    }
                },
                BRL: {
                    1: {
                        indicator: "Hypothesizing on possible business concept. Little knowledge or insight into market and competition",
                        description: "Vague and unspecific description of the potential business idea or business concept.\nLittle insight into the market and its potential/size.\nLittle knowledge or insight into competition and alternative solutions."
                    },
                    2: {
                        indicator: "First possible business concept described (e.g. NABC). Identified overall market and some competitors/alternatives",
                        description: "Described the proposed business concept in some structured form.\nOne or several markets or applications are identified and described on overall level.\nSome competitors and/or alternatives are identified and listed."
                    },
                    3: {
                        indicator: "Draft of business model in canvas (excl. revenues/costs). Described market potential and complete competitive overview",
                        description: "Draft of the business model in a canvas format (business model canvas/lean canvas) but typically without the revenues/cost parts.\nThe market potential and the market size is quantified with TAM and SAM.\nA more complete competitor overview with direct/indirect competitors."
                    },
                    4: {
                        indicator: "First version of full business model in canvas (incl. revenues/costs). First projections to show economic viability",
                        description: "There is a full business model in canvas format incl. details on possible revenues/costs.\nFirst economic projections with numbers to show the market potential and economic viability.\nMade a competitive analysis on your position and uniqueness/differentiation."
                    },
                    5: {
                        indicator: "Parts of business model tested on market. First version of revenue model incl. pricing hypotheses",
                        description: "The business model (at least parts of it) is tested against customers for verifying hypotheses.\nThere is a first version of a more detailed revenue model incl. pricing hypotheses.\nThe competitive position and differentiation is verified by market feedback."
                    },
                    6: {
                        indicator: "Full business model incl. pricing verified on customers (by test sales)",
                        description: "A complete business model incl. the pricing is tested vs. customers by test sales or similar.\nThe revenue model incl. pricing is updated and refined based on customer feedback.\nFirst more complete projections on revenue/costs."
                    },
                    7: {
                        indicator: "Product/market fit and customers payment willingness demonstrated. Attractive revenue vs cost projections",
                        description: "There is product/market fit meaning you can demonstrate significant customer interest and sales where customers show clear payment willingness.\nAttractive revenue vs cost projections being validated by sales and data.\nPreparations for scaling business with suppliers, sales channels."
                    },
                    8: {
                        indicator: "Sales and metrics show business model holds and can scale. Business model is fine-tuned",
                        description: "Sales and other metrics show the business model holds and is profitable.\nThe business model shows it can scale (potentially globally). Sales channels and supply chain are fully in place.\nBusiness model is set but is continuously fine-tuned to explore more revenue options."
                    },
                    9: {
                        indicator: "Business model is final and is scaling with growing recurring revenues",
                        description: "Business model is final and business is scaling with growing and recurring revenues.\nThe business scales by growing in new markets, new geographies, new segments.\nThere is a working business which is profitable and sustainable over time."
                    }
                },
                FRL: {
                    1: {
                        indicator: "Initial business idea with vague description. No clear view on funding needs and options",
                        description: "Initial business idea with unclear/poor description \u2013 no value proposition.\nNo insight into how much funding needed and for what.\nLittle insight into different funding options and funding types."
                    },
                    2: {
                        indicator: "Description of business concept (e.g. NABC). Defined funding needs and options for initial milestones",
                        description: "The business idea/business concept is reasonably well described incl. first version of value proposition.\nThe initial funding needs are mapped for initial key steps and milestones.\nThere is a basic plan with funding options for initial milestones (3-6 months)."
                    },
                    3: {
                        indicator: "Well described business concept and initial verification plan. First small soft funding secured",
                        description: "Well described business concept and initial verification plan (incl. hypothesis to verify, goals).\nBasic insight and knowledge of different financing options.\nObtained first small soft funding for commercial verification."
                    },
                    4: {
                        indicator: "Good pitch and short presentation of the business in place. Plan with different funding options over time",
                        description: "A succinct pitch (oral) and good written presentation of business concept is in place.\nThere is a more complete plan for funding needs/options over time (12-18 months).\nOverall budget and potential sources of funding."
                    },
                    5: {
                        indicator: "Investor oriented presentation and supporting material tested. Applied for and secured additional larger funding",
                        description: "There is an investor presentation (pitch deck) that has been tested and is being fine-tuned.\nSupporting material e.g. financial projections and budgets etc. are being developed.\nApplications for other types of funding e.g. grants or loans are prepared and filed."
                    },
                    6: {
                        indicator: "Improved investor presentation incl. business/financials. Decided on seeking private investors",
                        description: "There is an investor pitch deck that has been tested and fine-tuned which includes a focus on the business potential and financials.\nInsight into equity financing especially how investors think/evaluate.\nDecided to pursue equity funding and take in new owners."
                    },
                    7: {
                        indicator: "Team presents a solid investment case. Discussions with potential investors on-going around an offer",
                        description: "There is a team that can present well the investment case where key areas are in place such as prototype, traction/customer interest, market potential.\nThere is a complete business plan with financials and milestone plan.\nDiscussions with potential investors are on-going around a defined offer."
                    },
                    8: {
                        indicator: "Corporate order and structure enabling investment. Term sheet discussions with interested investor(s)",
                        description: "The company is reasonably structured e.g. in terms of agreements, ownership etc.\nThere is formal order in the company e.g. bookkeeping, documentation.\nClear interest and discussions on term sheet level with interested investor(s).\nAll necessary material often required by investors in place."
                    },
                    9: {
                        indicator: "Investment obtained. Additional investment needs and options continuously considered",
                        description: "Investment formally concluded with all relevant documentation and money obtained.\nAdditional future investment needs and options are continuously being considered for future."
                    }
                }
            };

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

                for (let lvl = 1; lvl <= 9; lvl++) {
                    const d = data[lvl];
                    if (!d) continue;
                    const opt = document.createElement('div');
                    opt.className = 'rl-dd-option';
                    opt.dataset.value = `Level ${lvl}`;

                    // Truncate indicator to ~40 chars for inline preview
                    const shortIndicator = d.indicator.length > 45 ? d.indicator.substring(0, 42) + '…' : d.indicator;

                    opt.innerHTML = `
                        <span class="rl-dd-opt-level">Lv ${lvl}</span>
                        <span class="rl-dd-opt-indicator">${shortIndicator}</span>
                        <div class="rl-dd-tooltip">
                            <div class="rl-tooltip-badge">${rlType} Level ${lvl}</div>
                            <div class="rl-tooltip-indicator">\u{1F3AF} ${d.indicator}</div>
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

