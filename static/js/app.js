document.addEventListener("DOMContentLoaded", () => {

    const logoScreen =
        document.getElementById("logoScreen");

    const welcomeScreen =
        document.getElementById("welcomeScreen");


    if (!logoScreen || !welcomeScreen) {
        return;
    }


    /*
     * المرحلة الأولى:
     * عرض شعار VYORA
     */
    setTimeout(() => {

        logoScreen.classList.add("hide");

        welcomeScreen.classList.add("show");

    }, 1800);


    /*
     * المرحلة الثانية:
     * بعد ظهور رسالة الترحيب،
     * الانتقال تلقائيًا إلى المتجر.
     */
    setTimeout(() => {

        window.location.href = "/home";

    }, 3500);

});
