# =========================================================
# SELLER SECTION
# =========================================================

def seller_required():
    user = current_user()

    if not user:
        return redirect(url_for("auth.login"))

    if user["role"] != "seller":
        flash("هذه الصفحة مخصصة للبائعين فقط.", "error")
        return redirect(url_for("home"))

    return None


@auth.route("/seller")
def seller():

    guard = seller_required()

    if guard:
        return guard

    user = current_user()

    store = Store.find_by_user_id(user["id"])

    products = []

    if store:
        products = Product.by_store(store["id"])

    return render_template(
        "seller.html",
        user=user,
        store=store,
        products=products
    )


@auth.route("/seller/edit", methods=["GET", "POST"])
def seller_edit():

    guard = seller_required()

    if guard:
        return guard

    user = current_user()

    store = Store.find_by_user_id(user["id"])

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        phone = request.form.get("phone", "").strip()
        wilaya = request.form.get("wilaya", "").strip()
        municipality = request.form.get("municipality", "").strip()

        if not name:
            flash("اسم المتجر مطلوب.", "error")
            return redirect(url_for("auth.seller_edit"))

        if store:
            Store.update(
                store["id"],
                name=name,
                description=description,
                phone=phone,
                wilaya=wilaya,
                municipality=municipality
            )
        else:
            Store.create(
                user_id=user["id"],
                name=name,
                description=description,
                phone=phone,
                wilaya=wilaya,
                municipality=municipality
            )

        flash("تم حفظ معلومات المتجر بنجاح 🏪", "success")

        return redirect(url_for("auth.seller"))


    return render_template(
        "seller_edit.html",
        user=user,
        store=store
    )


@auth.route("/seller/products/new", methods=["GET", "POST"])
def seller_product_new():

    guard = seller_required()

    if guard:
        return guard

    user = current_user()

    store = Store.find_by_user_id(user["id"])

    if not store:
        flash("أنشئ متجرك أولًا.", "error")
        return redirect(url_for("auth.seller_edit"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "0")
        discount = request.form.get("discount", "0")
        quantity = request.form.get("quantity", "0")
        category = request.form.get("category", "").strip()
        brand = request.form.get("brand", "").strip()
        images = request.form.get("images", "").strip()
        video = request.form.get("video", "").strip()
        delivery_wilayas = request.form.get(
            "delivery_wilayas",
            ""
        ).strip()

        if not name:
            flash("اسم المنتج مطلوب.", "error")
            return redirect(
                url_for("auth.seller_product_new")
            )

        try:
            price = float(price)
            discount = float(discount)
            quantity = int(quantity)

            if price < 0 or discount < 0 or quantity < 0:
                raise ValueError

        except ValueError:
            flash("تحقق من السعر والخصم والكمية.", "error")
            return redirect(
                url_for("auth.seller_product_new")
            )

        Product.create(
            store_id=store["id"],
            name=name,
            description=description,
            price=price,
            discount=discount,
            quantity=quantity,
            category=category,
            brand=brand,
            images=images,
            video=video,
            delivery_wilayas=delivery_wilayas
        )

        flash("تمت إضافة المنتج بنجاح 🎉", "success")

        return redirect(url_for("auth.seller"))


    return render_template(
        "seller_product_form.html",
        product=None,
        store=store
    )


@auth.route(
    "/seller/products/<int:product_id>/edit",
    methods=["GET", "POST"]
)
def seller_product_edit(product_id):

    guard = seller_required()

    if guard:
        return guard

    user = current_user()

    store = Store.find_by_user_id(user["id"])

    product = Product.find_by_id(product_id)

    if not store or not product:
        flash("المنتج غير موجود.", "error")
        return redirect(url_for("auth.seller"))

    if product["store_id"] != store["id"]:
        flash("ليس لديك صلاحية تعديل هذا المنتج.", "error")
        return redirect(url_for("auth.seller"))


    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "0")
        discount = request.form.get("discount", "0")
        quantity = request.form.get("quantity", "0")
        category = request.form.get("category", "").strip()
        brand = request.form.get("brand", "").strip()
        images = request.form.get("images", "").strip()
        video = request.form.get("video", "").strip()
        delivery_wilayas = request.form.get(
            "delivery_wilayas",
            ""
        ).strip()

        try:
            price = float(price)
            discount = float(discount)
            quantity = int(quantity)

            if price < 0 or discount < 0 or quantity < 0:
                raise ValueError

        except ValueError:
            flash("تحقق من السعر والخصم والكمية.", "error")
            return redirect(
                url_for(
                    "auth.seller_product_edit",
                    product_id=product_id
                )
            )

        Product.update(
            product_id,
            name=name,
            description=description,
            price=price,
            discount=discount,
            quantity=quantity,
            category=category,
            brand=brand,
            images=images,
            video=video,
            delivery_wilayas=delivery_wilayas
        )

        flash("تم تحديث المنتج بنجاح ✅", "success")

        return redirect(url_for("auth.seller"))


    return render_template(
        "seller_product_form.html",
        product=product,
        store=store
            )
