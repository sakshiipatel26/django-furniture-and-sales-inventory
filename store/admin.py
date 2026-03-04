from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin
from .models import Category, Product, Order, OrderItem, UserProfile, ProductImage
from django_summernote.admin import SummernoteModelAdmin
from .models import Product, Review
from .models import Advertisement
from django.contrib.auth.models import Group
from django.db.models import Count
from django.urls import reverse
from django.utils.timezone import now
from datetime import timedelta
from .models import Return, Exchange
from django.http import HttpResponse
import xlsxwriter
from io import BytesIO
from datetime import datetime
from django.db.models import Sum, Count, Max, Avg, Min, Q
from django.db.models.functions import TruncMonth
from django.urls import path
from django.contrib.admin import site
from django.contrib.auth import logout
from django.shortcuts import redirect

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1
    fields = ('name', 'price', 'discount_percentage', 'preview_image')
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />',
                obj.image.url)
        return "No Image"

    preview_image.short_description = 'Preview'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_primary', 'preview_image')
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px;" />',
                obj.image.url
            )
        return "No Image"

    preview_image.short_description = 'Preview'

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'start_date', 'end_date', 'preview_image')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('title',)
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 50px; object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return "No Image"

    preview_image.short_description = 'Preview'
    
    
@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin, SummernoteModelAdmin):
    list_display = ('tree_actions', 'indented_title', 'product_count')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    summernote_fields = ('description',)

    def product_count(self, obj):
        return obj.product_set.count()

    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('admin_thumbnail', 'name', 'category', 'formatted_price', 'discount_percentage', 'discounted_price_display','stock_status', 'has_ar_model')
    list_display_links = ('admin_thumbnail', 'name')
    search_fields = ('name', 'description')
    list_filter = ('category', 'discount_percentage', 'is_available', 'stock')
    readonly_fields = ('admin_preview','discounted_price_display')
    inlines = [ProductImageInline]

    def admin_thumbnail(self, obj):
        if obj.primary_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 4px" />',
                obj.primary_image.image.url
            )
        return "No Image"

    admin_thumbnail.short_description = 'Image'

    def admin_preview(self, obj):
        if obj.primary_image:
            return format_html(
                '<img src="{}" width="300" style="border-radius: 8px" />',
                obj.primary_image.image.url
            )
        return "No Image"

    admin_preview.short_description = 'Preview'

    def has_ar_model(self, obj):
        return bool(obj.ar_model)

    has_ar_model.boolean = True
    has_ar_model.short_description = 'AR Model'

    def discounted_price_display(self, obj):
        if obj.has_active_discount():
            return format_html(
                '<span style="color: #28a745;">₹{}</span> <small class="text-muted"><s>₹{}</s></small>',
                obj.discounted_price, obj.price
            )
        return f'₹{obj.price}'
    discounted_price_display.short_description = 'Final Price'

    def stock_status(self, obj):
        if not obj.is_available:
            return format_html('<span style="color: #dc3545;">Unavailable</span>')
        if obj.stock <= 0:
            return format_html('<span style="color: #dc3545;">Out of Stock</span>')
        if obj.stock < 10:
            return format_html('<span style="color: #ffc107;">Low Stock ({})</span>', obj.stock)
        return format_html('<span style="color: #28a745;">In Stock ({})</span>', obj.stock)
    stock_status.short_description = 'Stock Status'

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'price', 'description')
        }),
        ('Inventory', {
            'fields': ('stock', 'is_available'),
            'classes': ('collapse',)
        }),
        ('Discount', {
            'fields': ('discount_percentage', 'discount_start_date', 'discount_end_date', 'discounted_price_display'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('image', 'admin_preview', 'ar_model'),
            'classes': ('collapse',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'price', 'total_price')
    can_delete = False
    extra = 0

    def total_price(self, obj):
        return obj.get_total_cost()

    total_price.short_description = 'Total Price'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at', 'notification_status')
    list_filter = ('status', 'created_at', 'is_read')
    search_fields = ('user__username', 'shipping_address')
    inlines = [OrderItemInline]
    actions = ['mark_as_read']  # Removed 'generate_monthly_report'
    
    def notification_status(self, obj):
        if not obj.is_read:
            return format_html(
                '<span class="badge" style="background-color: #dc3545; color: white; '
                'padding: 5px 10px; border-radius: 10px;"><i class="fas fa-bell"></i> New</span>'
            )
        return ''
    notification_status.short_description = 'Status'

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected orders as read"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and not obj.is_read:
            obj.is_read = True
            obj.save()
        return super().change_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        today = now().date()
        
        # Ensure new order count is shown in both Orders page & Dashboard
        extra_context['new_orders'] = Order.objects.filter(
            created_at__date=today,
            is_read=False
        ).count()

        # Pass this data to admin index page
        site.index_template = 'admin/index.html'  
        return super().changelist_view(request, extra_context)


    def generate_monthly_report(self, request, queryset):
        # Create a new workbook and add a worksheet
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Monthly Sales Report')

        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B0082',
            'color': 'white',
            'align': 'center',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'center',
            'border': 1
        })

        # Write headers
        headers = [
            'Month-Year',
            'Total Orders',
            'Total Sales (₹)',
            'Average Order Value (₹)',
            'Top Selling Product',
            'Total Items Sold'
        ]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 20)  # Set column width

        # Get monthly data
        monthly_data = Order.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_orders=Count('id'),
            total_sales=Sum('total_amount'),
            avg_order_value=Sum('total_amount') / Count('id'),
        ).order_by('-month')

        # Write data
        row = 1
        for data in monthly_data:
            month = data['month'].strftime('%B %Y')
            
            # Get top selling product for this month
            top_product = OrderItem.objects.filter(
                order__created_at__month=data['month'].month,
                order__created_at__year=data['month'].year
            ).values('product__name').annotate(
                total_sold=Sum('quantity')
            ).order_by('-total_sold').first()

            # Get total items sold in this month
            total_items = OrderItem.objects.filter(
                order__created_at__month=data['month'].month,
                order__created_at__year=data['month'].year
            ).aggregate(total=Sum('quantity'))['total'] or 0

            # Write row data
            worksheet.write(row, 0, month, cell_format)
            worksheet.write(row, 1, data['total_orders'], cell_format)
            worksheet.write(row, 2, f"₹{data['total_sales']:,.2f}", cell_format)
            worksheet.write(row, 3, f"₹{data['avg_order_value']:,.2f}", cell_format)
            worksheet.write(row, 4, top_product['product__name'] if top_product else 'N/A', cell_format)
            worksheet.write(row, 5, total_items, cell_format)
            
            row += 1

        # Add a chart
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'Total Sales',
            'categories': f'=Monthly Sales Report!$A$2:$A${row}',
            'values': f'=Monthly Sales Report!$C$2:$C${row}',
        })
        chart.set_title({'name': 'Monthly Sales Trend'})
        chart.set_x_axis({'name': 'Month'})
        chart.set_y_axis({'name': 'Sales (₹)'})
        worksheet.insert_chart(f'H2', chart)

        workbook.close()
        
        # Create the HttpResponse with Excel content type
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=monthly_sales_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        
        return response

    generate_monthly_report.short_description = "Generate Monthly Sales Report"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-report/', 
                 self.admin_site.admin_view(self.generate_full_report), 
                 name='generate-full-report'),
        ]
        return custom_urls + urls

    def generate_full_report(self, request):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Create basic formats
        header_format = workbook.add_format({'bold': True})
        cell_format = workbook.add_format()
        currency_format = workbook.add_format({'num_format': '₹#,##0.00'})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        percent_format = workbook.add_format({'num_format': '0.00%'})

        # 1. Sales Summary Sheet
        sales_sheet = workbook.add_worksheet('Sales Summary')
        sales_headers = ['Period', 'Total Orders', 'Total Revenue', 'Avg Order Value', 
                        'Orders Growth', 'Revenue Growth']
        for col, header in enumerate(sales_headers):
            sales_sheet.write(0, col, header, header_format)
            
        monthly_data = Order.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            orders=Count('id'),
            revenue=Sum('total_amount'),
            avg_value=Sum('total_amount')/Count('id')
        ).order_by('-month')
        
        row = 1
        prev_orders = None
        prev_revenue = None
        for data in monthly_data:
            sales_sheet.write(row, 0, data['month'].strftime('%B %Y'), cell_format)
            sales_sheet.write(row, 1, data['orders'], cell_format)
            sales_sheet.write(row, 2, float(data['revenue']), currency_format)
            sales_sheet.write(row, 3, float(data['avg_value']), currency_format)
            
            # Calculate growth rates
            if prev_orders and prev_revenue:
                orders_growth = (data['orders'] - prev_orders) / prev_orders if prev_orders else 0
                revenue_growth = (data['revenue'] - prev_revenue) / prev_revenue if prev_revenue else 0
                sales_sheet.write(row, 4, orders_growth, percent_format)
                sales_sheet.write(row, 5, revenue_growth, percent_format)
            
            prev_orders = data['orders']
            prev_revenue = data['revenue']
            row += 1

        # 2. Customer Analysis
        customer_sheet = workbook.add_worksheet('Customer Analysis')
        customer_headers = ['Customer', 'Total Orders', 'Total Spent', 'Last Order', 
                        'Avg Order Value', 'First Order', 'Days Since Last Order']
        for col, header in enumerate(customer_headers):
            customer_sheet.write(0, col, header, header_format)
            
        customer_data = Order.objects.values(
            'user__username'
        ).annotate(
            total_orders=Count('id'),
            total_spent=Sum('total_amount'),
            last_order=Max('created_at'),
            first_order=Min('created_at'),
            avg_order=Avg('total_amount')
        ).order_by('-total_spent')
        
        row = 1
        for data in customer_data:
            customer_sheet.write(row, 0, data['user__username'], cell_format)
            customer_sheet.write(row, 1, data['total_orders'], cell_format)
            customer_sheet.write(row, 2, float(data['total_spent']), currency_format)
            customer_sheet.write(row, 3, data['last_order'].strftime('%Y-%m-%d'), date_format)
            customer_sheet.write(row, 4, float(data['avg_order']), currency_format)
            customer_sheet.write(row, 5, data['first_order'].strftime('%Y-%m-%d'), date_format)
            days_since = (datetime.now().date() - data['last_order'].date()).days
            customer_sheet.write(row, 6, days_since, cell_format)
            row += 1

        # 3. Product Performance
        product_sheet = workbook.add_worksheet('Product Performance')
        product_headers = ['Product', 'Category', 'Total Sales', 'Revenue', 'Stock Level', 
                        'Current Price', 'Discount', 'Status']
        for col, header in enumerate(product_headers):
            product_sheet.write(0, col, header, header_format)
            
        product_data = Product.objects.annotate(
            total_sales=Count('orderitem'),
            revenue=Sum('orderitem__price')
        ).values(
            'name', 'category__name', 'total_sales', 'revenue', 
            'stock', 'price', 'discount_percentage', 'is_available'
        ).order_by('-revenue')
        
        row = 1
        for data in product_data:
            product_sheet.write(row, 0, data['name'], cell_format)
            product_sheet.write(row, 1, data['category__name'], cell_format)
            product_sheet.write(row, 2, data['total_sales'] or 0, cell_format)
            product_sheet.write(row, 3, float(data['revenue'] or 0), currency_format)
            product_sheet.write(row, 4, data['stock'], cell_format)
            product_sheet.write(row, 5, float(data['price']), currency_format)
            product_sheet.write(row, 6, data['discount_percentage'], percent_format)
            status = 'Available' if data['is_available'] and data['stock'] > 0 else 'Unavailable'
            product_sheet.write(row, 7, status, cell_format)
            row += 1

        # 4. Category Performance
        category_sheet = workbook.add_worksheet('Category Analysis')
        category_headers = ['Category', 'Total Products', 'Active Products', 
                        'Total Sales', 'Total Revenue', 'Avg Product Price']
        for col, header in enumerate(category_headers):
            category_sheet.write(0, col, header, header_format)
            
        category_data = Category.objects.annotate(
            total_products=Count('product'),
            active_products=Count('product', filter=Q(product__is_available=True)),
            total_sales=Count('product__orderitem'),
            total_revenue=Sum('product__orderitem__price'),
            avg_price=Avg('product__price')
        ).values(
            'name', 'total_products', 'active_products', 
            'total_sales', 'total_revenue', 'avg_price'
        )
        
        row = 1
        for data in category_data:
            category_sheet.write(row, 0, data['name'], cell_format)
            category_sheet.write(row, 1, data['total_products'], cell_format)
            category_sheet.write(row, 2, data['active_products'], cell_format)
            category_sheet.write(row, 3, data['total_sales'] or 0, cell_format)
            category_sheet.write(row, 4, float(data['total_revenue'] or 0), currency_format)
            category_sheet.write(row, 5, float(data['avg_price'] or 0), currency_format)
            row += 1

        # Adjust column widths
        for sheet in [sales_sheet, customer_sheet, product_sheet, category_sheet]:
            sheet.set_column(0, 0, 25)  # First column wider
            sheet.set_column(1, 8, 15)  # Other columns

        workbook.close()
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=detailed_sales_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        return response

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',)
        }


class CustomAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        # Only show notifications if user is authenticated
        if request.user.is_authenticated:
            extra_context = extra_context or {}
            today = now().date()
            extra_context.update({
                'new_orders': Order.objects.filter(is_read=False).count(),
            })
        return super().index(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'analytics/',
                self.admin_view(self.analytics_view),
                name='analytics'
            ),
        ]
        return custom_urls + urls

    def analytics_view(self, request):
        context = {
            'title': 'Sales Analytics',
            'monthly_sales': Order.objects.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                total_sales=Sum('total_amount')
            ).order_by('-month')[:12],
            'top_products': Product.objects.annotate(
                total_sold=Sum('orderitem__quantity')
            ).order_by('-total_sold')[:10],
        }
        return self.render(request, 'admin/analytics.html', context)

# Replace default admin site
admin_site = CustomAdminSite(name='custom_admin')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type')
    list_filter = ('user_type',)
    search_fields = ('user_username', 'user_email')

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return ('user', 'user_type')
        return []


# Admin Site Customization
admin.site.site_header = 'Furniture Shop Administration'
admin.site.site_title = 'Furniture Shop Admin'
admin.site.index_title = 'Management Dashboard'


# Register your models so they appear in the Django admin panel
admin.site.register(Review)

admin.site.unregister(Group)

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['order__id', 'user__username']
    actions = ['approve_returns', 'reject_returns']

    def approve_returns(self, request, queryset):
        queryset.update(status='approved')
    approve_returns.short_description = "Approve selected returns"

    def reject_returns(self, request, queryset):
        queryset.update(status='rejected')
    reject_returns.short_description = "Reject selected returns"

@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'status', 'tracking_status', 'created_at']
    list_filter = ['status', 'tracking_status']
    search_fields = ['order__id', 'user__username']
    actions = ['approve_exchanges', 'reject_exchanges', 'mark_as_shipped', 'mark_as_delivered']

    def approve_exchanges(self, request, queryset):
        queryset.update(status='approved', tracking_status='pending')
    approve_exchanges.short_description = "Approve selected exchanges"

    def reject_exchanges(self, request, queryset):
        queryset.update(status='rejected', tracking_status='pending')
    reject_exchanges.short_description = "Reject selected exchanges"

    def mark_as_shipped(self, request, queryset):
        queryset.update(tracking_status='shipped')
    mark_as_shipped.short_description = "Mark selected exchanges as Shipped"

    def mark_as_delivered(self, request, queryset):
        queryset.update(tracking_status='delivered')
    mark_as_delivered.short_description = "Mark selected exchanges as Delivered"

#admin logout

def custom_logout(request):
    logout(request)
    return redirect('/admin/login/')  # Redirect to admin login after logout