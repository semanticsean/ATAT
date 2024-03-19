<script async src="https://www.googletagmanager.com/gtag/js?id={{ secrets.GTAG }}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  // Wrap secrets.GTAG in quotes to ensure proper JavaScript string syntax
  gtag('config', '{{ secrets.GTAG }}');
</script>
