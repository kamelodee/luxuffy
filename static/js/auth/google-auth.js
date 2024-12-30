const GOOGLE_CLIENT_ID = '162461087312-s2gmfbm4o30vjsiurib7c8f30lkc3o6n.apps.googleusercontent.com';

// Initialize Google Sign-In
function initGoogleSignIn() {
    google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleSignIn,
        auto_select: false,
        cancel_on_tap_outside: true
    });
}

// Handle the sign-in response
async function handleGoogleSignIn(response) {
    try {
        const result = await fetch('/api/auth/google', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id_token: response.credential
            })
        });

        const data = await result.json();

        if (result.ok) {
            // Store the token
            localStorage.setItem('token', data.access_token);
            
            // Update UI or redirect
            if (data.is_new_user) {
                window.location.href = '/onboarding';
            } else {
                window.location.href = '/dashboard';
            }
        } else {
            console.error('Google sign in failed:', data.error);
            alert('Failed to sign in with Google. Please try again.');
        }
    } catch (error) {
        console.error('Error during Google sign in:', error);
        alert('An error occurred during sign in. Please try again.');
    }
}

// Render the Google Sign-In button
function renderGoogleButton(elementId) {
    google.accounts.id.renderButton(
        document.getElementById(elementId),
        {
            theme: 'outline',
            size: 'large',
            type: 'standard',
            text: 'continue_with',
            shape: 'rectangular',
            logo_alignment: 'left',
            width: '100%'
        }
    );
}

// Handle sign out
function signOut() {
    if (localStorage.getItem('token')) {
        fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }
        }).then(() => {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }).catch(error => {
            console.error('Error during sign out:', error);
        });
    }
    
    // Also sign out from Google
    google.accounts.id.disableAutoSelect();
}

export { initGoogleSignIn, renderGoogleButton, signOut };
