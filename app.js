"use strict";

/*
 * DZ MARKET — Global Frontend Controller
 * مسؤول عن:
 * - الوضع الليلي/النهاري
 * - إظهار وإخفاء كلمات السر
 * - القوائم المتنقلة
 * - رسائل التأكيد
 * - اختصارات لوحة المفاتيح
 */

(function () {

    const THEME_KEY = "dzmarket-theme";


    /* =========================================
       THEME
    ========================================= */

    function applyTheme(theme) {

        const isDark = theme === "dark";

        document.body.classList.toggle("dark-mode", isDark);
        document.documentElement.setAttribute(
            "data-theme",
            isDark ? "dark" : "light"
        );

        document.querySelectorAll("[data-theme-toggle]")
            .forEach(function (button) {

                button.setAttribute(
                    "aria-label",
                    isDark
                        ? "تفعيل الوضع النهاري"
                        : "تفعيل الوضع الليلي"
                );

                button.setAttribute(
                    "title",
                    isDark
                        ? "الوضع النهاري"
                        : "الوضع الليلي"
                );

                const icon = button.querySelector("[data-theme-icon]");

                if (icon) {
                    icon.textContent = isDark ? "☀" : "☾";
                }
            });
    }


    function getPreferredTheme() {

        const saved = localStorage.getItem(THEME_KEY);

        if (saved === "dark" || saved === "light") {
            return saved;
        }

        if (
            window.matchMedia &&
            window.matchMedia("(prefers-color-scheme: dark)").matches
        ) {
            return "dark";
        }

        return "light";
    }


    function toggleTheme() {

        const current =
            document.body.classList.contains("dark-mode")
                ? "dark"
                : "light";

        const next = current === "dark"
            ? "light"
            : "dark";

        localStorage.setItem(THEME_KEY, next);
        applyTheme(next);
    }


    /* =========================================
       PASSWORD VISIBILITY
    ========================================= */

    function setupPasswordToggles() {

        document.querySelectorAll("[data-password-toggle]")
            .forEach(function (button) {

                if (button.dataset.passwordReady === "true") {
                    return;
                }

                button.dataset.passwordReady = "true";

                button.addEventListener("click", function () {

                    const targetId =
                        button.getAttribute("data-target");

                    const input =
                        document.getElementById(targetId);

                    if (!input) return;

                    const willShow =
                        input.type === "password";

                    input.type =
                        willShow ? "text" : "password";

                    /*
                     * هذا الكلاس يخلي SVG:
                     * العين المفتوحة ↔ العين المغلقة
                     */
                    button.classList.toggle(
                        "is-hidden",
                        willShow
                    );

                    button.setAttribute(
                        "aria-label",
                        willShow
                            ? "إخفاء كلمة السر"
                            : "إظهار كلمة السر"
                    );

                    button.setAttribute(
                        "title",
                        willShow
                            ? "إخفاء كلمة السر"
                            : "إظهار كلمة السر"
                    );
                });

            });
    }


    /* =========================================
       MOBILE MENU
    ========================================= */

    function setupMobileMenu() {

        const menuButton =
            document.querySelector("[data-mobile-menu-button]");

        const menu =
            document.querySelector("[data-mobile-menu]");

        if (!menuButton || !menu) return;

        if (menuButton.dataset.menuReady === "true") {
            return;
        }

        menuButton.dataset.menuReady = "true";

        menuButton.addEventListener("click", function () {

            const opened =
                menu.classList.toggle("is-open");

            menuButton.setAttribute(
                "aria-expanded",
                opened ? "true" : "false"
            );
        });
    }


    /* =========================================
       CONFIRM ACTIONS
    ========================================= */

    function setupConfirmActions() {

        document.querySelectorAll("[data-confirm]")
            .forEach(function (element) {

                if (element.dataset.confirmReady === "true") {
                    return;
                }

                element.dataset.confirmReady = "true";

                element.addEventListener("click", function (event) {

                    const message =
                        element.getAttribute("data-confirm") ||
                        "هل أنت متأكد؟";

                    if (!window.confirm(message)) {
                        event.preventDefault();
                    }
                });
            });
    }


    /* =========================================
       SEARCH SHORTCUT
    ========================================= */

    function setupSearchShortcut() {

        document.addEventListener("keydown", function (event) {

            if (
                event.key === "/" &&
                !event.ctrlKey &&
                !event.altKey &&
                !event.metaKey
            ) {

                const active =
                    document.activeElement;

                if (
                    active &&
                    (
                        active.tagName === "INPUT" ||
                        active.tagName === "TEXTAREA" ||
                        active.isContentEditable
                    )
                ) {
                    return;
                }

                const searchInput =
                    document.querySelector(
                        "[data-search-input], input[type='search']"
                    );

                if (searchInput) {
                    event.preventDefault();
                    searchInput.focus();
                }
            }

        });
    }


    /* =========================================
       ESCAPE
    ========================================= */

    function setupEscapeHandler() {

        document.addEventListener("keydown", function (event) {

            if (event.key !== "Escape") {
                return;
            }

            document.querySelectorAll(".is-open")
                .forEach(function (element) {

                    element.classList.remove("is-open");

                    if (
                        element.hasAttribute("aria-expanded")
                    ) {
                        element.setAttribute(
                            "aria-expanded",
                            "false"
                        );
                    }
                });
        });
    }


    /* =========================================
       THEME BUTTONS
    ========================================= */

    function setupThemeButtons() {

        document.querySelectorAll("[data-theme-toggle]")
            .forEach(function (button) {

                if (button.dataset.themeReady === "true") {
                    return;
                }

                button.dataset.themeReady = "true";

                button.addEventListener(
                    "click",
                    toggleTheme
                );
            });
    }


    /* =========================================
       AUTO DISMISS ALERTS
    ========================================= */

    function setupAlerts() {

        document.querySelectorAll(".alert[data-auto-dismiss]")
            .forEach(function (alert) {

                const seconds =
                    Number(
                        alert.getAttribute("data-auto-dismiss")
                    ) || 5;

                setTimeout(function () {

                    alert.style.opacity = "0";
                    alert.style.transform = "translateY(-5px)";

                    setTimeout(function () {
                        alert.remove();
                    }, 250);

                }, seconds * 1000);
            });
    }


    /* =========================================
       PUBLIC API
    ========================================= */

    window.DZMarket = {

        theme: {
            get: function () {
                return document.body.classList.contains("dark-mode")
                    ? "dark"
                    : "light";
            },

            set: function (theme) {

                if (
                    theme !== "dark" &&
                    theme !== "light"
                ) {
                    return;
                }

                localStorage.setItem(
                    THEME_KEY,
                    theme
                );

                applyTheme(theme);
            },

            toggle: toggleTheme
        },

        refreshPasswordToggles:
            setupPasswordToggles
    };


    /* =========================================
       INITIALIZATION
    ========================================= */

    function init() {

        applyTheme(getPreferredTheme());

        setupThemeButtons();
        setupPasswordToggles();
        setupMobileMenu();
        setupConfirmActions();
        setupSearchShortcut();
        setupEscapeHandler();
        setupAlerts();
    }


    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            init
        );

    } else {
        init();
    }

})();
