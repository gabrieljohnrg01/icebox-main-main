(() => {
    const ignoredTypes = new Set([
        'button',
        'checkbox',
        'color',
        'hidden',
        'image',
        'radio',
        'range',
        'reset',
        'submit',
    ]);

    function findLabel(field) {
        if (field.labels && field.labels.length) {
            return field.labels[0];
        }

        const container = field.closest('.form-group') || field.parentElement;
        return container ? container.querySelector('label') : null;
    }

    function labelText(label) {
        const clone = label.cloneNode(true);
        clone.querySelectorAll('.required-indicator, .optional-indicator').forEach((badge) => badge.remove());
        return clone.textContent.replace(/\s+/g, ' ').trim().replace(/\s*\*+$/, '');
    }

    function appendBadge(label, field) {
        const labelRow = label.parentElement;
        if (
            label.querySelector('.required-indicator, .optional-indicator')
            || (labelRow && labelRow.querySelector('.required-indicator, .optional-indicator'))
        ) {
            return;
        }

        const badge = document.createElement('span');
        badge.className = field.required ? 'required-indicator' : 'optional-indicator';
        badge.textContent = field.required ? 'Required' : 'Optional';
        badge.setAttribute('aria-hidden', 'true');
        label.appendChild(badge);
    }

    function appendHint(field, text) {
        const nextElement = field.nextElementSibling;
        if (nextElement && nextElement.classList.contains('field-hint')) {
            return;
        }

        const hint = document.createElement('span');
        hint.className = 'field-hint';
        hint.textContent = text;
        field.insertAdjacentElement('afterend', hint);
    }

    document.querySelectorAll('form input, form textarea, form select').forEach((field) => {
        const type = (field.type || '').toLowerCase();
        if (ignoredTypes.has(type)) {
            return;
        }

        const label = findLabel(field);
        if (!label) {
            return;
        }

        label.classList.add('form-field-label-row');
        appendBadge(label, field);

        const text = labelText(label);
        if (field.tagName === 'SELECT') {
            const promptOption = field.options[0];
            const updatePlaceholderStyle = () => {
                field.classList.toggle('is-placeholder', Boolean(promptOption && promptOption.value === '' && field.value === ''));
            };
            updatePlaceholderStyle();
            field.addEventListener('change', updatePlaceholderStyle);
            return;
        }

        if (field.type === 'date' || field.type === 'datetime-local' || field.type === 'time') {
            appendHint(field, 'Choose a date or time.');
            return;
        }

        if (field.type === 'file') {
            appendHint(field, field.multiple ? 'Choose one or more files.' : 'Choose a file to upload.');
            return;
        }

        if (!field.placeholder && !field.value) {
            field.placeholder = `Enter ${text.toLowerCase()}`;
        }
    });
})();
