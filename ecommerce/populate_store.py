import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.utils.text import slugify
from shop.models import Category, Brand, Product, ProductImage

def run_seed():
    print("Starting store population with media images and appropriate names...")

    # 1. Categories
    category_data = [
        {'name': 'Electronics', 'slug': 'electronics', 'description': 'Smart devices, audio, and personal computing'},
        {'name': 'Fashion', 'slug': 'fashion', 'description': 'Trendy apparel, premium footwear, and accessories'},
        {'name': 'Home & Living', 'slug': 'home-living', 'description': 'Modern home furniture, seating, and decor'},
        {'name': 'Sports & Outdoors', 'slug': 'sports', 'description': 'Fitness, running shoes, and outdoor gear'},
        {'name': 'Beauty & Personal Care', 'slug': 'beauty-personal-care', 'description': 'Skincare, hair care, and grooming essentials'},
    ]
    
    categories = {}
    for cat_info in category_data:
        cat, _ = Category.objects.get_or_create(
            slug=cat_info['slug'],
            defaults={'name': cat_info['name'], 'description': cat_info['description']}
        )
        cat.name = cat_info['name']
        cat.description = cat_info['description']
        cat.save()
        categories[cat_info['slug']] = cat

    # Also check if existing 'sports' category or 'home-living' exists
    for cat in Category.objects.all():
        categories[cat.slug] = cat
        categories[cat.name] = cat

    # 2. Brands
    brand_names = [
        'Apple', 'Samsung', 'Nike', 'Adidas', 'Sony',
        'Dell', 'Garnier', 'Indulekha', 'Boult Audio',
        'NJSJ', 'Artisan Care', 'HomeComfort', 'ComfortDesk',
        'TrailMaster', 'BionicMove'
    ]
    brands = {}
    for b_name in brand_names:
        b_slug = slugify(b_name)
        brand, _ = Brand.objects.get_or_create(
            slug=b_slug,
            defaults={'name': b_name}
        )
        brand.name = b_name
        brand.save()
        brands[b_name] = brand

    # 3. Clean up inappropriate dummy product "Test P" (id=5)
    test_p = Product.objects.filter(id=5).first()
    if test_p and ('Test' in test_p.name or 'test' in test_p.slug):
        print(f"Renaming and repurposing placeholder test product: {test_p.name}")
        test_p.name = "Garnier Bright Complete Vitamin C Face Wash (100g)"
        test_p.slug = "garnier-bright-complete-vitamin-c-face-wash-100g"
        test_p.category = categories['beauty-personal-care']
        test_p.brand = brands['Garnier']
        test_p.price = 9.99
        test_p.original_price = 12.99
        test_p.image = "products/61Vp0-XHx2L.jpg"
        test_p.description = "Enriched with Yuzu Lemon extract and Vitamin C, this clarifying face wash effectively cleanses dirt and dullness to reveal fresh, glowing skin."
        test_p.stock = 50
        test_p.available = True
        test_p.featured = False
        test_p.save()
        print(f"Repurposed product ID 5 into: {test_p.name}")

    # 4. Products definition
    products_catalog = [
        # Apple
        {
            'slug': 'iphone-15-pro',
            'name': 'Apple iPhone 15 Pro (128GB - Natural Titanium)',
            'category': categories['electronics'],
            'brand': brands['Apple'],
            'price': 999.00,
            'original_price': 1099.00,
            'image': 'products/iphone_15_pro.jpg',
            'description': 'The ultimate iPhone experience forged in aerospace-grade titanium, featuring the groundbreaking A17 Pro chip, customizable Action button, and versatile 48MP Pro camera system with 3x optical zoom.',
            'stock': 15,
            'featured': True,
        },
        # Nike
        {
            'slug': 'nike-air-max-270',
            'fallback_slug': 'nike-air-max',
            'name': 'Nike Air Max 270 Athletic Lifestyle Sneakers',
            'category': categories['fashion'],
            'brand': brands['Nike'],
            'price': 150.00,
            'original_price': 180.00,
            'image': 'products/nike_air_max.jpg',
            'description': "Boasting Nike's biggest heel Air unit yet, the Nike Air Max 270 delivers super-soft cushioning and a sleek, running-inspired silhouette engineered for all-day comfort and street style.",
            'stock': 28,
            'featured': True,
        },
        # Sony
        {
            'slug': 'sony-wh-1000xm5',
            'name': 'Sony WH-1000XM5 Wireless Noise Cancelling Headphones',
            'category': categories['electronics'],
            'brand': brands['Sony'],
            'price': 349.00,
            'original_price': 399.00,
            'image': 'products/sony_wh1000xm5.jpg',
            'description': 'Industry-leading noise cancellation powered by two processors and 8 microphones. Extraordinary sound quality with high-resolution LDAC audio, crystal-clear hands-free calling, and up to 30 hours of battery life.',
            'stock': 20,
            'featured': True,
        },
        # Adidas
        {
            'slug': 'adidas-ultraboost-light',
            'fallback_slug': 'adidas-ultraboost',
            'name': 'Adidas Ultraboost Light High-Performance Running Shoes',
            'category': categories['sports'],
            'brand': brands['Adidas'],
            'price': 180.00,
            'original_price': 210.00,
            'image': 'products/adidas_ultraboost.jpg',
            'description': 'Experience epic energy with the lightest Ultraboost ever made. Features responsive Boost midsole cushioning, breathable Primeknit+ textile upper, and Continental Rubber outsole grip.',
            'stock': 22,
            'featured': False,
        },
        # Garnier Face Wash (if not handled by id=5)
        {
            'slug': 'garnier-bright-complete-vitamin-c-face-wash-100g',
            'name': 'Garnier Bright Complete Vitamin C Face Wash (100g)',
            'category': categories['beauty-personal-care'],
            'brand': brands['Garnier'],
            'price': 9.99,
            'original_price': 12.99,
            'image': 'products/61Vp0-XHx2L.jpg',
            'description': 'Enriched with Yuzu Lemon extract and Vitamin C, this clarifying face wash effectively cleanses dirt and dullness to reveal fresh, glowing skin.',
            'stock': 50,
            'featured': False,
        },
        # Garnier Serum Cream
        {
            'slug': 'garnier-bright-complete-vitamin-c-serum-cream-uv',
            'name': 'Garnier Bright Complete Vitamin C Serum Cream UV (50g)',
            'category': categories['beauty-personal-care'],
            'brand': brands['Garnier'],
            'price': 14.50,
            'original_price': 18.00,
            'image': 'products/71nUe95xR1L.jpg',
            'description': 'Ultra-lightweight brightening serum cream enriched with Vitamin C and UV filters that protects against harmful UV rays while visibly fading dark spots and boosting skin radiance.',
            'stock': 35,
            'featured': False,
        },
        # Garnier SkinActive Kit
        {
            'slug': 'garnier-skinactive-vitamin-c-glow-kit',
            'name': 'Garnier SkinActive Vitamin C Complete Glow Kit',
            'category': categories['beauty-personal-care'],
            'brand': brands['Garnier'],
            'price': 39.99,
            'original_price': 52.00,
            'image': 'products/download_2.jpeg',
            'description': 'Complete 4-piece radiance-boosting daily skincare kit containing Micellar Cleansing Water, Vitamin C Booster Serum, Day Moisturizing Cream, and Super UV Sunscreen SPF 50.',
            'stock': 25,
            'featured': True,
        },
        # Indulekha Hair Oil
        {
            'slug': 'indulekha-bringha-ayurvedic-hair-oil-100ml',
            'name': 'Indulekha Bringha Ayurvedic Anti-Hair Fall Oil (100ml)',
            'category': categories['beauty-personal-care'],
            'brand': brands['Indulekha'],
            'price': 16.99,
            'original_price': 21.00,
            'image': 'products/26313_S7-8901030929502.webp',
            'description': '100% Ayurvedic medicine clinically proven to grow new hair and reduce hair fall. Enriched with Bringharaj, Svetakutaja, and Amla extracts, with an innovative Selfie Comb applicator for targeted scalp nourishment.',
            'stock': 40,
            'featured': True,
            'gallery_images': [
                'products/images_3.jpeg',
                'products/Top_9_Hair_Care_Brands_in_India_For_Men_and_Women_1.jpg'
            ]
        },
        # Men's Eco Grooming Kit
        {
            'slug': 'eco-friendly-mens-grooming-shaving-spa-kit',
            'name': "Artisan Care Eco-Friendly Men's Grooming & Shaving Spa Kit",
            'category': categories['beauty-personal-care'],
            'brand': brands['Artisan Care'],
            'price': 45.00,
            'original_price': 60.00,
            'image': 'products/WhatsApp_Image_2021-10-14_at_10.59.54_AM.webp',
            'description': 'Handcrafted eco-luxury men’s shaving and skincare set featuring a precision safety razor, natural bristle shave brush, organic sandalwood comb, beard nourishment drops, and botanical cleansing soap.',
            'stock': 20,
            'featured': False,
        },
        # Samsung Galaxy S22 Ultra
        {
            'slug': 'samsung-galaxy-s22-ultra-5g-smartphone',
            'name': 'Samsung Galaxy S22 Ultra 5G Smartphone (256GB)',
            'category': categories['electronics'],
            'brand': brands['Samsung'],
            'price': 899.00,
            'original_price': 1199.00,
            'image': 'products/images_1.jpeg',
            'description': 'Samsung flagship smartphone with embedded S-Pen stylus, groundbreaking Nightography 108MP Quad camera with 100x Space Zoom, brilliant 6.8-inch Dynamic AMOLED 2X 120Hz display, and 5000mAh all-day battery.',
            'stock': 14,
            'featured': True,
        },
        # Dell Laptop
        {
            'slug': 'dell-inspiron-14-everyday-business-laptop',
            'name': 'Dell Inspiron 14 High-Performance Laptop',
            'category': categories['electronics'],
            'brand': brands['Dell'],
            'price': 649.00,
            'original_price': 799.00,
            'image': 'products/images_2.jpeg',
            'description': 'Crisp 14-inch Full HD anti-glare laptop powered by Intel Core processor, 16GB DDR4 high-speed memory, 512GB PCIe NVMe SSD, backlit ergonomic keyboard, and Windows 11 Home.',
            'stock': 12,
            'featured': False,
        },
        # Boult Audio Earbuds
        {
            'slug': 'boult-audio-true-wireless-earbuds',
            'name': 'Boult Audio True Wireless Bluetooth Earbuds',
            'category': categories['electronics'],
            'brand': brands['Boult Audio'],
            'price': 29.99,
            'original_price': 49.99,
            'image': 'products/shopping_1.webp',
            'description': 'TWS Bluetooth earbuds featuring dual-tone charging case, environmental noise cancellation (ENC), boom bass acoustic drivers, ultra-low latency gaming mode, and 40-hour total playback.',
            'stock': 45,
            'featured': False,
        },
        # NJSJ RGB Gaming Speakers
        {
            'slug': 'njsj-2-1-rgb-gaming-desktop-speakers-with-subwoofer',
            'name': 'NJSJ 2.1 RGB Gaming Desktop Speakers with Subwoofer',
            'category': categories['electronics'],
            'brand': brands['NJSJ'],
            'price': 49.99,
            'original_price': 69.99,
            'image': 'products/65a3f902b22d436c02334a0d-njsj-computer-speakers-with-subwoofer.jpg',
            'description': 'Immersive 2.1 multimedia sound system delivering powerful bass through a dedicated wooden subwoofer, dynamic color-cycling RGB illumination, and independent bass and treble adjustment dials.',
            'stock': 24,
            'featured': False,
        },
        # Hi-Fi Floorstanding Tower Speakers
        {
            'slug': 'sony-hi-fi-floorstanding-tower-speaker-system',
            'name': 'Sony Hi-Fi Stereo Floorstanding Tower Speaker System',
            'category': categories['electronics'],
            'brand': brands['Sony'],
            'price': 299.00,
            'original_price': 399.00,
            'image': 'products/hifi_tower_speakers.jpg',
            'description': 'Audiophile-grade 3-way floorstanding tower speakers featuring dual high-output woofers, silk dome tweeters, and tuned bass-reflex ports for immersive concert-quality acoustics.',
            'stock': 8,
            'featured': False,
        },
        # Smartwatch
        {
            'slug': 'smartwatch-with-bluetooth-calling-fitness-tracker',
            'name': 'Smartwatch with Bluetooth Calling & Fitness Tracker',
            'category': categories['electronics'],
            'brand': brands['Samsung'],
            'price': 69.99,
            'original_price': 99.99,
            'image': 'products/71zoBbV66L.jpg',
            'description': '1.85-inch HD vibrant touch screen smartwatch with Bluetooth phone calling, voice assistant, real-time heart rate and SpO2 tracking, sleep monitoring, 100+ fitness sport modes, and 7-day battery life.',
            'stock': 35,
            'featured': True,
            'gallery_images': [
                'products/cc0c9f44-e01a-430d-9c5a-9d1103cb4100.__CR00600600_PT0_SX300_V1___.jpg',
                'products/64885eb2-7aa0-4f72-9f0a-feb7807618e6.__CR00600600_PT0_SX300_V1___.jpg',
                'products/53cf432a-748d-4e1a-ad9a-1ae96bfac19f.__CR00600600_PT0_SX300_V1___.jpg',
                'products/71HqlGY1rgL._AC_UL116_SR116116_.jpg'
            ]
        },
        # Men's Driving Loafers
        {
            'slug': 'mens-classic-suede-driving-loafers',
            'name': "Men's Classic Suede Driving Loafers & Moccasins",
            'category': categories['fashion'],
            'brand': brands['Nike'],
            'price': 79.99,
            'original_price': 110.00,
            'image': 'products/images.jpeg',
            'description': 'Handcrafted Italian-style slip-on driving moccasins made with supple suede leather, alligator-embossed vamp, metal horsebit buckle accent, and flexible non-slip studded rubber outsole.',
            'stock': 30,
            'featured': True,
        },
        # Convertible Sleeper Chair
        {
            'slug': 'convertible-sleeper-armchair-with-pull-out-bed',
            'name': 'HomeComfort 3-in-1 Convertible Sleeper Armchair Bed',
            'category': categories['home-living'],
            'brand': brands['HomeComfort'],
            'price': 349.00,
            'original_price': 449.00,
            'image': 'products/images_4.jpeg',
            'description': 'Multi-functional space-saving 3-in-1 convertible sleeper chair that easily transitions into a lounge recliner or bed. Features high-resilience foam cushioning, pull-out ottoman, and soft linen upholstery.',
            'stock': 12,
            'featured': False,
        },
        # Ergonomic Mesh Office Chair
        {
            'slug': 'ergonomic-high-back-mesh-office-chair',
            'name': 'ComfortDesk Ergonomic High-Back Mesh Office Chair',
            'category': categories['home-living'],
            'brand': brands['ComfortDesk'],
            'price': 189.99,
            'original_price': 249.99,
            'image': 'products/images_5.jpeg',
            'description': 'Premium ergonomic executive office chair with breathable high-tensile mesh back, 2D adjustable headrest, adaptive lumbar support, flip-up armrests, and SGS-certified pneumatic gas lift.',
            'stock': 20,
            'featured': False,
        },
        # Modern Luxury Sofa Set
        {
            'slug': 'modern-luxury-3-piece-living-room-sofa-set',
            'name': 'HomeComfort Modern Luxury 3-Piece Living Room Sofa Set',
            'category': categories['home-living'],
            'brand': brands['HomeComfort'],
            'price': 1299.00,
            'original_price': 1650.00,
            'image': 'products/shopping.webp',
            'description': 'Sophisticated 3-piece living room furniture suite comprising a plush 3-seater sofa and two matching accent armchairs upholstered in durable stain-resistant textured fabric with solid wood frame and legs.',
            'stock': 6,
            'featured': True,
        },
        # Outdoor Hiking & Wilderness Kit
        {
            'slug': 'outdoor-hiking-wilderness-camping-gear-kit',
            'name': 'TrailMaster Outdoor Hiking & Wilderness Camping Gear Kit',
            'category': categories['sports'],
            'brand': brands['TrailMaster'],
            'price': 219.00,
            'original_price': 289.00,
            'image': 'products/Hiking-101-Guide-Gear-GettyImages-1256366704.webp',
            'description': 'All-in-one backcountry expedition gear set including a heavy-duty waxed canvas rucksack, waterproof all-terrain trekking boots, vintage kerosene lantern, wide-brim bush hat, and survival camp axe.',
            'stock': 15,
            'featured': True,
        },
        # Powered Lifting Exoskeleton
        {
            'slug': 'ergonomic-powered-spine-support-lifting-exoskeleton',
            'name': 'BionicMove Ergonomic Powered Spine Support Exoskeleton',
            'category': categories['sports'],
            'brand': brands['BionicMove'],
            'price': 799.00,
            'original_price': 999.00,
            'image': 'products/44172_2024_180_Fig1_HTML.png',
            'description': 'Cutting-edge wearable lifting assistance exosuit engineered with dual IMU motion sensors, ribbon cable assist actuators, and an adjustable BOA tensioning system to eliminate lower back and lumbar fatigue.',
            'stock': 8,
            'featured': False,
        },
    ]

    for p_info in products_catalog:
        slug = p_info['slug']
        fallback_slug = p_info.get('fallback_slug')
        
        # Check if product exists by primary slug or fallback slug
        product = Product.objects.filter(slug=slug).first()
        if not product and fallback_slug:
            product = Product.objects.filter(slug=fallback_slug).first()
            if product:
                product.slug = slug
        
        if not product:
            product = Product(slug=slug)

        product.name = p_info['name']
        product.category = p_info['category']
        product.brand = p_info['brand']
        product.price = p_info['price']
        product.original_price = p_info['original_price']
        product.image = p_info['image']
        product.description = p_info['description']
        product.stock = p_info['stock']
        product.available = True
        product.featured = p_info['featured']
        product.save()
        print(f"Saved product: {product.name} (Image: {product.image})")

        # Gallery images
        gallery = p_info.get('gallery_images', [])
        for g_img in gallery:
            ProductImage.objects.get_or_create(
                product=product,
                image=g_img,
                defaults={'alt_text': f"{product.name} - View"}
            )

    print("\nFinished seeding successfully!")
    print(f"Total Products in DB: {Product.objects.count()}")
    for p in Product.objects.all().order_by('id'):
        print(f"  [{p.id}] {p.name} | Cat: {p.category.name} | Price: ${p.price} | Img: {p.image}")

if __name__ == '__main__':
    run_seed()
