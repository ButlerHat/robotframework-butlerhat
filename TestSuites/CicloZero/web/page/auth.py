import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth


def login():
    with open(st.secrets.configs.auth_config) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    name, authentication_status, username = authenticator.login('Login', 'main')
    return name, authentication_status, username, authenticator


def auth_header(authenticator, username, name, authentication_status):
    if authentication_status:

        with st.expander('Manage Account', expanded=False):
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
        
        # Welcome message
        with col1:
            st.markdown(f'<span style="color:grey">Welcome</span> *{name}*', unsafe_allow_html=True)
        
        # Reset Password button
        with col3:
            reset_placeholder = st.empty()
            
            if not hasattr(st.session_state, 'show_reset'):
                st.session_state.show_reset = False
            
            # If clicks reset password, show always reset password form, until close button is pressed
            is_reset = reset_placeholder.button('Reset password', key='reset_password')
            st.session_state.show_reset = is_reset or st.session_state.show_reset
        
        # Create user button
        with col2:
            create_placeholder = st.empty()

            if not hasattr(st.session_state, 'show_create'):
                st.session_state.show_create = False

            # If clicks create user, show always create user form, until close button is pressed
            if username == 'david' or username == 'ciclozero':
                is_create = create_placeholder.button('Create user', key='create_user')
                st.session_state.show_create = is_create or st.session_state.show_create


        # Display reset password form
        if st.session_state.show_reset:
            # If closes no show form
            close_placeholder = col4.empty()
            if close_placeholder.button('Close', key='close_reset_password'):
                close_placeholder.empty()
                st.session_state.show_reset = False
            else:
                create_placeholder.empty()
                reset_placeholder.empty()
                reset_password(authenticator, username)
                st.stop()

        # Display create user form
        if st.session_state.show_create:
            # If closes no show form
            close_placeholder = col4.empty()
            # reset_placeholder.empty()
            if close_placeholder.button('Close', key='close_reset_password'):
                close_placeholder.empty()
                st.session_state.show_create = False
            else:
                reset_placeholder.empty()
                create_placeholder.empty()
                create_user(authenticator)
                st.stop()
        
        # Logout
        with col4:
            authenticator.logout('Logout', 'main', key='unique_key')


def reset_password(authenticator, username):
    try:
        rc = authenticator.reset_password(username, 'Reset password')
    except Exception as e:
        st.error(e)
        return
    
    if rc:
        with open(st.secrets.configs.auth_config) as file:
            config = yaml.load(file, Loader=SafeLoader)
        config['credentials'] = authenticator.credentials
        with open(st.secrets.configs.auth_config, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        st.success('Password modified successfully')


def create_user(authenticator):
    try:
        rc = authenticator.register_user('Register user', preauthorization=False)
    except Exception as e:
        st.error(e)
        return
    
    if rc:
        with open(st.secrets.configs.auth_config) as file:
            config = yaml.load(file, Loader=SafeLoader)
        config['credentials'] = authenticator.credentials
        with open(st.secrets.configs.auth_config, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        st.success('User created successfully')