document.addEventListener('DOMContentLoaded', function() {
  var renderTeamPhotoButton = document.getElementById('renderTeamPhoto');
  var refreshPhotoButton = document.getElementById('refreshPhoto');
  var heroImage = document.querySelector('.hero-image');

  function handleButtonClick() {
    heroImage.src = "{{ url_for('static', filename='loading.gif') }}";
    fetch("{{ url_for('generate_hero_image') }}")
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        heroImage.src = "data:image/png;base64," + data.image_data;
      });
  }

  if (renderTeamPhotoButton) {
    renderTeamPhotoButton.addEventListener('click', handleButtonClick);
  }

  if (refreshPhotoButton) {
    refreshPhotoButton.addEventListener('click', handleButtonClick);
  }
});