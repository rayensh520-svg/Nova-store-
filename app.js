/* =========================================================
   DZ MARKET 🇩🇿
   Global Frontend Controller
   ========================================================= */

(function () {
    "use strict";

    const THEME_KEY = "dzmarket-theme";

    /* =====================================================
       THEME
       ===================================================== */

    function applyTheme(theme) {
        const isDark = theme === "dark";

        document.body.classList.toggle("dark-mode", isDark);

        document.documentElement.setAttribute(
            "data-theme",
            isDark ? "dark" : "light"
        );

        localStorage.setItem(
            THEME_KEY,
            isDark ? "dark" : "light"
        );

        updateThemeButtons(isDark);
    }

    function getInitialTheme() {
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

    function updateThemeButtons(isDark) {
        document
            .querySelectorAll("[data-theme-toggle]")
            .forEach(button => {

                button.setAttribute(
                    "aria-label",
                    isDark
                        ? "تفعيل الوضع الفاتح"
                        : "تفعيل الوضع الليلي"
                );

                button.setAttribute(
                    "title",
                    isDark
                        ? "الوضع الفاتح"
                        : "الوضع الليلي"
                );

                const sun = button.querySelector(
                    "[data-icon-sun]"
                );

                const moon = button.querySelector(
                    "[data-icon-moon]"
                );

                if (sun) {
                    sun.style.display =
                        isDark ? "block" : "none";
                }

                if (moon) {
                    moon.style.display =
                        isDark ? "none" : "block";
                }
            });
    }

    function toggleTheme() {
        const dark =
            document.body.classList.contains("dark-mode");

        applyTheme(dark ? "light" : "dark");
    }

    /* Apply immediately */
    applyTheme(getInitialTheme());

    /* =====================================================
       DOM READY
       ===================================================== */

    document.addEventListener("DOMContentLoaded", function () {

        /* Theme buttons */
        document
            .querySelectorAll("[data-theme-toggle]")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    toggleTheme
                );
            });

        updateThemeButtons(
            document.body.classList.contains("dark-mode")
        );

        /* =================================================
           PASSWORD VISIBILITY
           ================================================= */

        document
            .querySelectorAll("[data-password-toggle]")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    function () {

                        const targetId =
                            this.getAttribute(
                                "data-password-toggle"
                            );

                        const input =
                            document.getElementById(targetId);

                        if (!input) return;

                        const visible =
                            input.type === "text";

                        input.type =
                            visible ? "password" : "text";

                        this.setAttribute(
                            "aria-label",
                            visible
                                ? "إظهار كلمة المرور"
                                : "إخفاء كلمة المرور"
                        );

                        this.setAttribute(
                            "title",
                            visible
                                ? "إظهار كلمة المرور"
                                : "إخفاء كلمة المرور"
                        );

                        /* Change SVG state if available */
                        this.classList.toggle(
                            "password-visible",
                            !visible
                        );
                    }
                );
            });

        /* =================================================
           AUTO DISMISS ALERTS
           ================================================= */

        document
            .querySelectorAll(
                ".alert[data-auto-dismiss]"
            )
            .forEach(alert => {

                const delay =
                    Number(
                        alert.dataset.autoDismiss
                    ) || 5000;

                window.setTimeout(() => {

                    alert.style.opacity = "0";
                    alert.style.transform =
                        "translateY(-5px)";

                    window.setTimeout(() => {
                        alert.remove();
                    }, 250);

                }, delay);
            });

        /* =================================================
           CONFIRM ACTIONS
           ================================================= */

        document
            .querySelectorAll("[data-confirm]")
            .forEach(element => {

                element.addEventListener(
                    "click",
                    function (event) {

                        const message =
                            this.dataset.confirm ||
                            "هل أنت متأكد؟";

                        if (!window.confirm(message)) {
                            event.preventDefault();
                        }
                    }
                );
            });

        /* =================================================
           MOBILE MENU
           ================================================= */

        const menuButton =
            document.querySelector(
                "[data-mobile-menu]"
            );

        const mobileMenu =
            document.querySelector(
                "[data-mobile-menu-panel]"
            );

        if (menuButton && mobileMenu) {

            menuButton.addEventListener(
                "click",
                function () {

                    const opened =
                        mobileMenu.classList.toggle(
                            "is-open"
                        );

                    menuButton.setAttribute(
                        "aria-expanded",
                        opened ? "true" : "false"
                    );
                }
            );
        }

        /* =================================================
           SEARCH SHORTCUT
           ================================================= */

        document.addEventListener(
            "keydown",
            function (event) {

                const tag =
                    document.activeElement?.tagName;

                const typing =
                    tag === "INPUT" ||
                    tag === "TEXTAREA" ||
                    tag === "SELECT";

                if (
                    event.key === "/" &&
                    !typing
                ) {

                    const search =
                        document.querySelector(
                            "[data-search-input]"
                        );

                    if (search) {

                        event.preventDefault();

                        search.focus();
                    }
                }
            }
        );

        /* =================================================
           ESCAPE
           ================================================= */

        document.addEventListener(
            "keydown",
            function (event) {

                if (event.key !== "Escape") {
                    return;
                }

                document
                    .querySelectorAll(
                        ".is-open"
                    )
                    .forEach(element => {
                        element.classList.remove(
                            "is-open"
                        );
                    });
            }
        );
    });

    /* =====================================================
       PUBLIC API
       ===================================================== */

    window.DZMarket = {

        toggleTheme,

        setTheme: function (theme) {

            if (
                theme !== "dark" &&
                theme !== "light"
            ) {
                return;
            }

            applyTheme(theme);
        },

        getTheme: function () {
            return document.body.classList.contains(
                "dark-mode"
            )
                ? "dark"
                : "light";
        }
    };

})();
