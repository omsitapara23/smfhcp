$('#invite-form').on('submit', function(event){
    event.preventDefault();
    console.log("invite form submitted!")
    invite();
});

$('#inviteModalCloseButton').on('click', function(event){
    $('#msgDiv').html('');
    $('#msgDiv').removeClass("alert alert-success alert-danger")
});

$('#loginForm').on('submit', function(event){
    event.preventDefault();
    console.log("login form submitted!")
    login();
});

$('#signUpForm').on('submit', function(event){
    event.preventDefault();
    console.log("signup form submitted!")
    signUp();
});

$('#signUpFormCloseButton').on('click', function(event){
    $('#errorDiv').html('');
    $('#errorDiv').removeClass("alert alert-success alert-danger")
});

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function invite() {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    $.ajax({
        url : "/send_invite/",
        type : "POST",
        data : { email : $('#exampleInputEmail1').val()},
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },

        success : function(json) {
            console.log("Invite is sent")
            $('#exampleInputEmail1').val('');
            $('#msgDiv').removeClass("alert alert-success alert-danger")
            if (json.success) {
                $('#msgDiv').addClass("alert alert-success").html(json.message)
            } else {
                $('#msgDiv').addClass("alert alert-danger").html(json.message)
            }

        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

function login() {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    $('#msgDivLogin').html('')
    $('#msgDivLogin').removeClass("alert alert-danger")
    $.ajax({
        url : "login_user/",
        type : "POST",
        data : { user_name : $('#exampleUsername1').val(), password : $('#exampleInputPassword1').val()},
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
        success : function(json) {
            if (json.redirect) {
                window.location.href = json.redirect_url;
            } else {
                console.log("Username or password wrong")
                $('#exampleUsername1').val('')
                $('#exampleInputPassword1').val('')
                $('#msgDivLogin').addClass("alert alert-danger").html(json.message)
            }
        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}

function checkValidity() {
    $('#errorDiv').html('')
    $('#errorDiv').removeClass("alert alert-danger")
    var nameRegex = /^[a-zA-Z0-9_]+$/;
    var validUsername = $("#exampleInputUsername1").val().match(nameRegex);
    if(validUsername == null){
        $('#errorDiv').addClass("alert alert-danger").html("Your user name is not valid. Only characters A-Z, a-z, 0-9 and '_' are acceptable.");
        console.log("username entered wrong");
        return false;
    }
    var password = $("#txtPassword").val();
    var confirmPassword = $("#txtConfirmPassword").val();
    if (password != confirmPassword) {
        $('#errorDiv').addClass("alert alert-danger").html("Password and Confirm password do not match.");
        console.log("password wrong");
        return false;
    }
    return true;
}

function signUp() {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    if(checkValidity()) {
        $.ajax({
            url : "signup_email/",
            type : "POST",
            data : { user_name : $('#exampleInputUsername1').val(), password : $('#txtPassword').val(), email : $('#exampleInputEmail1').val()},
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success : function(json) {
                if (json.redirect) {
                    window.location.href = json.redirect_url;
                } else {
                    console.log("Username or email already exists")
                    $('#exampleInputUsername1').val('')
                    $('#exampleInputEmail1').val('')
                    $('#txtPassword').val('')
                    $('#txtConfirmPassword').val('')
                    $('#errorDiv').addClass("alert alert-danger").html(json.message)
                }
            },
            error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    }
}
