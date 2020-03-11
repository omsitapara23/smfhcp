$('#createProfileForm').on('submit', function(event){
    event.preventDefault();
    console.log("create profile form submitted!")
    createProfile();
});

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function checkValidity() {
    $('#errorDiv').html('')
    $('#errorDiv').removeClass("alert alert-danger")
    var nameRegex = /^[a-zA-Z0-9_]+$/;
    var validUsername = $("#exampleUsername1").val().match(nameRegex);
    if(validUsername == null){
        $('#errorDiv').addClass("alert alert-danger").html("Your user name is not valid. Only characters A-Z, a-z and '_' are acceptable.");
        console.log("username wrong");
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

function createProfile() {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    if(checkValidity()) {
        $.ajax({
            url : "/create_profile/",
            type : "POST",
            data : { user_name : $('#exampleUsername1').val(), password : $('#txtPassword').val(),
            email : $('#exampleInputEmail1').val(), otp: $('#otpField').val(), firstName : $('#firstName').val(),
            lastName : $('#lastName').val(), qualification : $('#qualification').val(), profession : $('#profession').val(),
            institution : $('#institution').val(), researchInterests : $('#researchInterests').val(),
            clinicalInterests : $('#clinicalInterests').val() },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success : function(json) {
                if (json.redirect) {
                    window.location.href = json.redirect_url;
                } else {
                    console.log("Error shown.")
                    $('#exampleUsername1').val('')
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