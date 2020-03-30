$('#forgotPasswordForm').on('submit', function(event){
    event.preventDefault();
    console.log("forgotPasswordForm submitted!")
    forgotPassword();
});

$('#forgotPasswordModalCloseButton').on('click', function(event){
    $('#forgotPasswordModalErrorDiv').html('');
    $('#forgotPasswordModalErrorDiv').removeClass("alert alert-success alert-danger")
});

function forgotPassword() {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    $.ajax({
        url : "/forgot_password/",
        type : "POST",
        data : { user_name : $('#forgotPasswordModalUsername1').val()},
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
            $('#forgotPasswordModalErrorDiv').removeClass("alert-success alert alert-danger").html("<img src=\"/static/images/loading.gif\" style=\"width: 35px; height: 35px;\">")
        },
        success : function(json) {
            $('#forgotPasswordModalUsername1').val('');
            $('#forgotPasswordModalErrorDiv').removeClass("alert alert-success alert-danger")
            if (json.success) {
                $('#forgotPasswordModalErrorDiv').addClass("alert alert-success").html(json.message)
            } else {
                $('#forgotPasswordModalErrorDiv').addClass("alert alert-danger").html(json.message)
            }
        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}
