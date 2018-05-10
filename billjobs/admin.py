import csv
from django import forms
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.core.urlresolvers import reverse
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from .models import Bill, BillLine, Service, UserProfile, Revenue, Subscription
from django.utils import timezone
from django.db.models import Sum

class BillLineInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BillLineInlineForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['service'].queryset = Service.objects.filter(Q(is_available=True) | Q(name=self.instance.service.name))
            print(self.fields['service'].choices)
        else:
            self.fields['service'].queryset = Service.objects.filter(is_available=True)

    class Meta:
        model = BillLine
        fields = ('service', 'quantity', 'total', 'note')

class BillLineInline(admin.TabularInline):
    model = BillLine
    extra = 1
    form = BillLineInlineForm


class BillAdmin(admin.ModelAdmin):
    readonly_fields = ('number', 'billing_date', 'amount')
    exclude = ('issuer_address', 'billing_address')
    inlines = [BillLineInline]
    list_display = ('__str__', 'coworker_name_link', 'amount', 'billing_date',
            'isPaid', 'pdf_file_url', 'paiement')
    list_editable = ('isPaid',)
    list_filter = ('isPaid', )
    search_fields = ('user__first_name', 'user__last_name', 'number', 'amount')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(BillAdmin, self).formfield_for_foreignkey(
                                                db_field, request, **kwargs)
        if db_field.rel.to == User:
            field.initial = request.user.id
            field.label_from_instance = self.get_user_label
        return field

    def get_user_label(self, user):
        name = user.get_full_name()
        username = user.username
        return (name and name != username and '%s (%s)' % (name, username)
                or username)

    def coworker_name_link(self, obj):
        ''' Create a link to user admin edit view '''
        return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:auth_user_change', args=(obj.user.id,)),
                obj.coworker_name())
    coworker_name_link.short_description = _('Coworker name')

    def pdf_file_url(self, obj):
        return format_html(
                '<a href="{}">{}.pdf</a>',
                reverse('generate-pdf', args=(obj.id,)),
                obj.number)
    pdf_file_url.short_description=_('Download invoice')

    def paiement(self, obj):
        if obj.isPaid == False:
            lien = format_html(
            '<a href="https://stripe.com">Payer sur Stripe</a>'
            )
            # lien = 'Payer sur Stripe'
            return lien
        else:
            return 'Effectué'

    # def testt(self, foo):
    #     # sequence = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    #     # sequence = 1
    #     # while sequence <= 12:
    #     # for element in sequence:
    #     # return Bill.objects.filter(billing_date__month=4, billing_date__year=2017, isPaid=True).aggregate(Sum('amount'))['amount__sum']
    #     return Bill.objects.filter(billing_date__month=4, billing_date__year=2017, isPaid=True).aggregate(Sum('amount'))['amount__sum']


class RequiredInlineFormSet(BaseInlineFormSet):
    """
    Generates an inline formset that is required
    """

    def _construct_form(self, i, **kwargs):
        """
        Override the method to change the form attribute empty_permitted
        """
        form = super(RequiredInlineFormSet, self)._construct_form(i, **kwargs)
        form.empty_permitted = False
        return form

class UserProfileAdmin(admin.StackedInline):
    model = UserProfile
    formset = RequiredInlineFormSet

class UserForm(UserChangeForm):

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

class UserAdmin(UserAdmin):
    inlines = (UserProfileAdmin, )
    fieldsets = (
            (None, {
                'fields': ('username', 'password')
                }),
            (_('Personal info'), {
                'fields': ('first_name', 'last_name', 'email')
                }),
            (_('Permissions'), {
                'classes': ('collapse',),
                'fields': ('is_active', 'is_staff', 'is_superuser',
                           'groups', 'user_permissions')
                }),
            (_('Important dates'), {
                'classes': ('collapse',),
                'fields': ('last_login', 'date_joined')
                })
            )
    list_display = ('username', 'get_full_name', 'email')
    actions = ['export_email']
    form = UserForm

    def export_email(self, request, queryset):
        """ Export emails of selected account """
        response = HttpResponse(content_type='text/csv')

        writer = csv.writer(response)
        for email in queryset.values_list('email'):
            writer.writerow(email)

        return response
    export_email.short_description = _('Export email of selected users')

class ServiceAdmin(admin.ModelAdmin):
    model = Service
    list_display = ('__str__', 'price', 'is_available')
    list_editable = ('is_available',)
    list_filter = ('is_available',)

class RevenueAdmin(admin.ModelAdmin):
    model = Revenue
    # list_display = ('month', 'amount', 'total_revenue')
    list_display = ('annee', 'janvier', 'fevrier', 'mars', 'avril', 'mai',
    'juin', 'juillet', 'aout', 'septembre', 'octobre', 'novembre', 'decembre',
    'CA_annuel')
    total = 0

    # Revenue.april.value() = 8000

    def current_month(self, foo):
        current_month = timezone.now().month

    def total_rev(self, r):
        total = 0
        r = Revenue.objects.all()
        for i in r:

            return i


    # def testt(self, obj):
    #     if obj.annee == 2018:
    #         obj.january = 30000
    #         # obj.january.save()
    #         return obj.january
    #     else:
    #         return 'Hello world'

    def CA_annuel(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def janvier(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=1, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=1, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=1, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=1, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=1, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def fevrier(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=2, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=2, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=2, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=2, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=2, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def mars(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=3, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=3, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=3, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=3, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=3, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def avril(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=4, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=4, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=4, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=4, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=4, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def mai(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=5, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=5, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=5, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=5, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=5, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def juin(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=6, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=6, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=6, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=6, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=6, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def juillet(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=7, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=7, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=7, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=7, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=7, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def aout(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=8, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=8, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=8, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=8, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=8, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def septembre(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=9, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=9, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=9, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=9, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=9, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def octobre(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=10, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=10, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=10, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=10, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=10, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def novembre(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=1, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=11, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=11, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=11, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=11, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']

    def decembre(self, obj):
        if obj.annee == 2018:
            return Bill.objects.filter(billing_date__month=12, billing_date__year=2018).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2017:
            return Bill.objects.filter(billing_date__month=12, billing_date__year=2017).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2016:
            return Bill.objects.filter(billing_date__month=12, billing_date__year=2016).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2015:
            return Bill.objects.filter(billing_date__month=12, billing_date__year=2015).aggregate(Sum('amount'))['amount__sum']
        if obj.annee == 2014:
            return Bill.objects.filter(billing_date__month=12, billing_date__year=2014).aggregate(Sum('amount'))['amount__sum']


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    list_display = ('service', 'Abonnement_annuel')

    def Abonnement_annuel(self, obj):
        if obj.service == 'Full Time':
            return BillLine.objects.filter(service__is_available=True,
            service__pk=1, bill__billing_date__year=2017).count()
        if obj.service == 'Mid Time':
            return BillLine.objects.filter(service__is_available=True,
            service__pk=2, bill__billing_date__year=2017).count()
        if obj.service == 'Meeting 1 day':
            return BillLine.objects.filter(service__is_available=True,
            service__pk=3, bill__billing_date__year=2017).count()


admin.site.register(Bill, BillAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Revenue, RevenueAdmin)
admin.site.register(Subscription, SubscriptionAdmin)

# User have to be unregistered
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
