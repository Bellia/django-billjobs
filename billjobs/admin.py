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
    ordering = ['-billing_date']

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
            '<a href="https://stripe.com" target="_blank">Payer sur Stripe</a>'
            )
            return lien
        else:
            return 'Effectué'


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


current_year = timezone.now().year
current_month = timezone.now().month
previous_month = current_month - 1


class RevenueAdmin(admin.ModelAdmin):
    model = Revenue
    # list_display = ('month', 'amount', 'total_revenue')
    list_display = ('annee', 'janvier', 'fevrier', 'mars', 'avril', 'mai',
    'juin', 'juillet', 'aout', 'septembre', 'octobre', 'novembre', 'decembre',
    'CA_annuel')
    ordering = ['-annee']


    def CA_annuel(self, obj):

        # current_month = timezone.now().month
        # previous_month = current_month - 1
        # current_year = timezone.now().year
        if current_year == obj.annee:
            data = (Bill.objects.filter(billing_date__year=current_year, billing_date__month__lte=previous_month).aggregate(Sum('amount'))['amount__sum']) / previous_month * 12
            return format_html('CA prévisionnel <strong style="color: purple" title="Estimation du CA annuel : somme des mois finis divisée par le nombre de mois finis multipliés par 12">{}</strong>', data)
            # return (Bill.objects.filter(billing_date__year=current_year, billing_date__month__lte=previous_month).aggregate(Sum('amount'))['amount__sum']) / previous_month * 12
        else:
            data =  Bill.objects.filter(billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
            return data

    def monthly_revenue(self, obj, month):
        data =  Bill.objects.filter(billing_date__month=month, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == month and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def janvier(self, obj):
        return self.monthly_revenue(obj, 1)


    def fevrier(self, obj):
        m = 2
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def mars(self, obj):
        m = 3
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def avril(self, obj):
        m = 4
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def mai(self, obj):
        m = 5
        data = Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data


    def juin(self, obj):
        m = 6
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def juillet(self, obj):
        m = 7
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def aout(self, obj):
        m = 8
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def septembre(self, obj):
        m = 9
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def octobre(self, obj):
        m = 10
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def novembre(self, obj):
        m = 11
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

    def decembre(self, obj):
        m = 12
        data =  Bill.objects.filter(billing_date__month=m, billing_date__year=obj.annee).aggregate(Sum('amount'))['amount__sum']
        if current_month == m and current_year == obj.annee:
            return format_html('<strong style="color: purple">{}</strong>', data)
        else:
            return data

class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    list_display = ('service', 'Abonnement_annuel_2018', 'Abonnement_annuel_2017')

    def Abonnement_annuel_2017(self, obj):
        # if obj.service == 'Full Time':
        #     return BillLine.objects.filter(service__is_available=True,
        #     service__pk=1, bill__billing_date__year=2017).count()
        # if obj.service == 'Mid Time':
        #     return BillLine.objects.filter(service__is_available=True,
        #     service__pk=2, bill__billing_date__year=2017).count()
        # if obj.service == 'Meeting 1 day':
        #     return BillLine.objects.filter(service__is_available=True,
        #     service__pk=3, bill__billing_date__year=2017).count()
        return BillLine.objects.filter(service__is_available=True,
        service__name=obj.service, bill__billing_date__year=2017).count()

    def Abonnement_annuel_2018(self, obj):
        return BillLine.objects.filter(service__is_available=True,
        service__name=obj.service, bill__billing_date__year=2018).count()


admin.site.register(Bill, BillAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Revenue, RevenueAdmin)
admin.site.register(Subscription, SubscriptionAdmin)

# User have to be unregistered
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
