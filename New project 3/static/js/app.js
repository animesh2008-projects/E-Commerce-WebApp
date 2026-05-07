const pageLoader = document.getElementById('pageLoader');
const cartCount = document.getElementById('cartCount');
const feedbackModal = document.getElementById('feedbackModal');
const authModal = document.getElementById('authModal');
const navToggle = document.getElementById('navToggle');
const siteNav = document.getElementById('siteNav');

const openModal = (modal, message) => {
    if (!modal) return;
    if (message) {
        const messageNode = modal.querySelector('p');
        if (messageNode) messageNode.textContent = message;
    }
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
};

const closeModal = (modal) => {
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
};

const bumpCartCount = (value) => {
    if (!cartCount) return;
    cartCount.textContent = value;
    cartCount.classList.remove('is-bumping');
    void cartCount.offsetWidth;
    cartCount.classList.add('is-bumping');
};

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.18 });

document.querySelectorAll('.reveal').forEach((node) => revealObserver.observe(node));

window.addEventListener('load', () => {
    if (pageLoader) {
        pageLoader.classList.add('is-hidden');
    }
});

document.querySelectorAll('[data-transition]').forEach((link) => {
    link.addEventListener('click', (event) => {
        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || link.target === '_blank') return;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        document.body.classList.add('is-leaving');
        window.setTimeout(() => {
            window.location.href = href;
        }, 170);
    });
});

document.querySelectorAll('[data-close-modal]').forEach((button) => {
    button.addEventListener('click', () => {
        closeModal(feedbackModal);
        closeModal(authModal);
    });
});

[feedbackModal, authModal].forEach((modal) => {
    if (!modal) return;
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal(modal);
        }
    });
});

if (navToggle && siteNav) {
    navToggle.addEventListener('click', () => {
        siteNav.classList.toggle('is-open');
    });
}

const postForm = async (form) => {
    const response = await fetch(form.action, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: new URLSearchParams(new FormData(form)),
        credentials: 'same-origin',
    });

    let data = {};
    try {
        data = await response.json();
    } catch (error) {
        data = {};
    }

    return { response, data };
};

document.querySelectorAll('.js-add-to-cart').forEach((form) => {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        const originalLabel = button ? button.textContent : '';
        if (button) {
            button.disabled = true;
            button.textContent = 'Adding...';
        }

        try {
            const { response, data } = await postForm(form);
            if (response.status === 401) {
                openModal(authModal, data.message);
                return;
            }
            if (!response.ok) {
                openModal(feedbackModal, data.message || 'Unable to update your cart right now.');
                return;
            }

            bumpCartCount(data.cart_count ?? cartCount?.textContent ?? '0');
            form.classList.add('is-complete');
            openModal(feedbackModal, data.message || 'Cart updated successfully.');
        } catch (error) {
            openModal(feedbackModal, 'Something went wrong while updating your cart.');
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = originalLabel;
            }
        }
    });
});

document.querySelectorAll('.js-cart-update').forEach((form) => {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const itemCard = form.closest('[data-cart-item]');
        try {
            const { response, data } = await postForm(form);
            if (!response.ok) {
                openModal(feedbackModal, data.message || 'Unable to update the cart.');
                return;
            }
            if (itemCard) {
                const totalNode = itemCard.querySelector('[data-line-total]');
                if (totalNode) {
                    totalNode.textContent = `$${data.item.line_total}`;
                }
            }
            const summaryTotal = document.getElementById('summaryTotal');
            if (summaryTotal) summaryTotal.textContent = `$${data.cart_total}`;
            const summaryCount = document.getElementById('summaryCount');
            if (summaryCount) summaryCount.textContent = data.cart_count;
            bumpCartCount(data.cart_count);
            openModal(feedbackModal, data.message || 'Cart quantity updated.');
        } catch (error) {
            openModal(feedbackModal, 'Unable to update the cart right now.');
        }
    });
});

document.querySelectorAll('.js-cart-remove').forEach((form) => {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const itemCard = form.closest('[data-cart-item]');
        try {
            const { response, data } = await postForm(form);
            if (!response.ok) {
                openModal(feedbackModal, data.message || 'Unable to remove the item.');
                return;
            }
            if (itemCard) itemCard.remove();
            if (data.cart_count === 0) {
                window.location.reload();
                return;
            }
            const summaryTotal = document.getElementById('summaryTotal');
            if (summaryTotal) summaryTotal.textContent = `$${data.cart_total}`;
            const summaryCount = document.getElementById('summaryCount');
            if (summaryCount) summaryCount.textContent = data.cart_count;
            bumpCartCount(data.cart_count);
            openModal(feedbackModal, data.message || 'Item removed.');
        } catch (error) {
            openModal(feedbackModal, 'Unable to remove the item right now.');
        }
    });
});

document.querySelectorAll('.js-checkout-form').forEach((form) => {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        const originalLabel = button ? button.textContent : '';
        if (button) {
            button.disabled = true;
            button.textContent = 'Processing...';
        }
        try {
            const { response, data } = await postForm(form);
            if (!response.ok) {
                openModal(feedbackModal, data.message || 'Unable to place the order.');
                return;
            }
            bumpCartCount(0);
            window.location.href = '/orders/';
        } catch (error) {
            openModal(feedbackModal, 'Unable to place the order right now.');
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = originalLabel;
            }
        }
    });
});
