const scriptURL = 'https://script.google.com/macros/s/AKfycbzXcrDTNVEqmNSmbfcG3LEl3lYVvXjQXVRkmcCGjW1ry_3a7ovf11smVmvARdxpbl4/exec'
  const form = document.forms['submit-to-google-sheet']

  form.addEventListener('submit', e => {
    e.preventDefault()
    fetch(scriptURL, { method: 'POST', body: new FormData(form)})
      .then(response => {
        setTimeout(function(){
          alert("data entered!");
        },1);
        form.reset();
      })
      .catch(error => console.error('Error!', error.message))
    
  })