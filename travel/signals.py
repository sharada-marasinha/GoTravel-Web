from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Use get_or_create to prevent IntegrityError
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        # Get or create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=instance)
        profile.save()
    except Exception:
        # Handle any other exceptions gracefully
        pass
