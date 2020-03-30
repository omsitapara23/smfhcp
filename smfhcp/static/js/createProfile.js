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
    var qualifications = []
    var researchInterests = []
    var clinicalInterests = []
    $('input[name="qualification[]"]').each(function() {
        qualifications.push($(this).val());
    });
    $('input[name="researchInterests[]"]').each(function() {
        researchInterests.push($(this).val());
    });
    $('input[name="clinicalInterests[]"]').each(function() {
        clinicalInterests.push($(this).val());
    });
    var formData = new FormData();
    formData.append('user_name', $('#exampleUsername1').val())
    formData.append('password', $('#txtPassword').val())
    formData.append('email', $('#exampleInputEmail1').val())
    formData.append('otp', $('#otpField').val())
    formData.append('firstName', $('#firstName').val())
    formData.append('lastName', $('#lastName').val())
    formData.append('qualification', JSON.stringify({ 'qualifications': qualifications }))
    formData.append('profession', $('#profession').val())
    formData.append('institution', $('#institution').val())
    formData.append('researchInterests', JSON.stringify({ 'researchInterests': researchInterests }))
    formData.append('clinicalInterests', JSON.stringify({ 'clinicalInterests': clinicalInterests }))
    formData.append('profilePicture', $('#upload')[0].files[0])
    if(checkValidity()) {
        $.ajax({
            url : "/create_profile/",
            type : "POST",
            data : formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
                $('#errorDiv').removeClass("alert-success alert alert-danger").html("<img src=\"/static/images/loading.gif\" style=\"width: 35px; height: 35px;\">")
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

$("#qualAddButton").click(function(){
    $("#qualWrapper").append("<div class=\"input-group\" style=\"margin-top: 10px;\">" +
                    "<input name=\"qualification[]\" type=\"text\" required=\"true\" class=\"form-control\">" +
                    "<span class=\"input-group-btn\">" +
                        "<button class=\"btn btn-success btn-remove plus-minus\" type=\"button\">" +
                            "<i class=\"fa fa-minus\"></i>" +
                        "</button>" +
                    "</span>" +
                "</div>");
});

$("#researchIntAddButton").click(function(){
    $("#researchIntWrapper").append("<div class=\"input-group\" style=\"margin-top: 10px;\">" +
                    "<input name=\"researchInterests[]\" type=\"text\" required=\"true\" class=\"form-control\">" +
                    "<span class=\"input-group-btn\">" +
                        "<button class=\"btn btn-success btn-remove plus-minus\" type=\"button\">" +
                            "<i class=\"fa fa-minus\"></i>" +
                        "</button>" +
                    "</span>" +
                "</div>");
});

$("#clinicalIntAddButton").click(function(){
    $("#clinicalIntWrapper").append("<div class=\"input-group\" style=\"margin-top: 10px;\">" +
                    "<input name=\"clinicalInterests[]\" type=\"text\" required=\"true\" class=\"form-control\">" +
                    "<span class=\"input-group-btn\">" +
                        "<button class=\"btn btn-success btn-remove plus-minus\" type=\"button\">" +
                            "<i class=\"fa fa-minus\"></i>" +
                        "</button>" +
                    "</span>" +
                "</div>");
});

$(document).ready(function() {
    $(document).on("click",".btn-remove", function(e){
		e.preventDefault();
		 $(this).parents('.input-group:first').remove();
	})
}
);
