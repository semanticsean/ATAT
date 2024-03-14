<script async src="https://www.googletagmanager.com/gtag/js?id={{ secrets.GTAG }}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', '{{ secrets.GTAG }}');
</script>
