from .models import UserProfile

def user_profile(request):
    """
    Add user profile to context for all templates
    """
    if request.user.is_authenticated:
        try:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            return {'user_profile': profile}
        except:
            return {'user_profile': None}
    return {'user_profile': None}
