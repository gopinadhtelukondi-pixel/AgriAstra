def show_weather_skeleton(placeholder):
    """Display a short loading placeholder only while weather data is requested."""
    placeholder.markdown("""
    <div style="background:white;border:1px solid #E2E8E0;border-radius:15px;padding:18px">
      <div style="height:15px;width:40%;background:#E8F1E7;border-radius:7px"></div>
      <div style="height:34px;width:62%;background:#EEF2EC;border-radius:8px;margin-top:14px"></div>
      <div style="height:12px;width:78%;background:#F2F4F0;border-radius:7px;margin-top:12px"></div>
    </div>
    """,unsafe_allow_html=True)

def show_advisory_skeleton(placeholder):
    """Show the answer placeholder while evidence retrieval and generation are active."""
    placeholder.markdown("""
    <div style="background:white;border:1px solid #E2E8E0;border-radius:15px;padding:18px">
      <div style="height:15px;width:32%;background:#E8F1E7;border-radius:7px"></div>
      <div style="height:12px;width:92%;background:#EEF2EC;border-radius:7px;margin-top:18px"></div>
      <div style="height:12px;width:84%;background:#EEF2EC;border-radius:7px;margin-top:10px"></div>
      <div style="height:12px;width:67%;background:#F2F4F0;border-radius:7px;margin-top:10px"></div>
    </div>
    """,unsafe_allow_html=True)

